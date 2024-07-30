using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Diagnostics.Contracts;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.Dafny;

namespace placeholder
{
    public enum DafnyErrorType
    {
        Assertion,
        AssertBy,
        Precondition,
        Related,
        Postcondition,
        LoopInvariant,
        LHSValue,
        Forall,
        Calc,
        Unknown
    }

    public class DafnyError
    {
        public string File { get; set; }
        public int Line { get; set; }
        public int Column { get; set; }
        public string ErrorMessage { get; set; }
        public string LineContent { get; set; }
        public DafnyErrorType ErrorType { get; set; }
        public List<DafnyError> RelatedErrors { get; set; } = new List<DafnyError>();
        public Statement SourceStatement { get; set; }

        public override string ToString()
        {
            string relatedErrorsStr = string.Join("\n", RelatedErrors);
            return $"File: {File}, Line: {Line}, Column: {Column}, Error: {ErrorMessage}, Content: {LineContent}\nRelated Errors:\n{relatedErrorsStr}";
        }

        public Node findStatementNode(Program program, Uri uri)
        {
            var position = new DafnyPosition(this.Line - 1, this.Column);
            var node_assert = program.FindNode<Statement>(uri, position);
            var node_list = ErrorLocation.ExtractFindNodeChain(
                program,
                uri,
                position,
                null,
                (INode node) => node is Statement
            );
            if (node_assert == null)
            {
                foreach (var module in program.Modules())
                {
                    node_assert = module.FindNode<Statement>(uri, position);
                    if (node_assert != null)
                    {
                        break;
                    }
                }
                // DONT DO this because we dont want to find pre and post conditions!!!
                // if (node_assert == null)
                // {
                //     throw new Exception("Node not found");
                // }
            }
            this.SourceStatement = node_assert;
            return this.SourceStatement;
        }
    }

    public static class ErrorParser
    {
        public static List<DafnyError> ParseErrors(string errorString)
        {
            var errorList = new List<DafnyError>();
            var lines = errorString.Split(new[] { Environment.NewLine }, StringSplitOptions.None);
            var regex = new Regex(
                @"^(?<file>.+\.dfy)\((?<line>\d+),(?<column>\d+)\): (?<error>.+)$"
            );

            DafnyError currentError = null;
            for (int i = 0; i < lines.Length; i++)
            {
                var match = regex.Match(lines[i]);
                if (match.Success)
                {
                    var file = match.Groups["file"].Value;
                    var line = int.Parse(match.Groups["line"].Value);
                    var column = int.Parse(match.Groups["column"].Value);
                    var errorMessage = match.Groups["error"].Value;

                    var newError = new DafnyError
                    {
                        File = file,
                        Line = line,
                        Column = column,
                        ErrorMessage = errorMessage,
                        ErrorType = GetErrorType(errorMessage)
                    };

                    var lineContent = string.Empty;
                    if (i + 2 < lines.Length && lines[i + 2].StartsWith($"{line} |"))
                    {
                        lineContent = lines[i + 2].Substring(lines[i + 2].IndexOf('|') + 1).Trim();
                    }
                    newError.LineContent = lineContent;
                    if (
                        newError.ErrorType == DafnyErrorType.Assertion
                        && newError.LineContent.EndsWith("by {")
                    )
                    {
                        newError.ErrorType = DafnyErrorType.AssertBy;
                    }

                    if (currentError != null && errorMessage.Contains("Related location"))
                    {
                        currentError.RelatedErrors.Add(newError);
                    }
                    else
                    {
                        if (currentError != null)
                        {
                            errorList.Add(currentError);
                        }
                        currentError = newError;
                    }

                    // Skip the next few lines as they are part of the current error
                    i += 3;
                }
            }

            if (currentError != null)
            {
                errorList.Add(currentError);
            }

            return errorList;
        }

        private static DafnyErrorType GetErrorType(string errorMessage)
        {
            if (errorMessage.Contains("assertion might not hold"))
            {
                return DafnyErrorType.Assertion;
            }
            else if (errorMessage.Contains("precondition for this call could not be proved"))
            {
                return DafnyErrorType.Precondition;
            }
            else if (errorMessage.Contains("related location"))
            {
                return DafnyErrorType.Related;
            }
            else if (
                errorMessage.Contains("a postcondition could not be proved on this return path")
            )
            {
                return DafnyErrorType.Postcondition;
            }
            else if (
                errorMessage.Contains(
                    "cannot establish the existence of LHS values that satisfy the such-that predicate"
                )
            )
            {
                return DafnyErrorType.LHSValue;
            }
            else if (errorMessage.Contains("this invariant could not be proved to be"))
            {
                return DafnyErrorType.LoopInvariant;
            }
            else if (errorMessage.Contains("possible violation of postcondition of forall"))
            {
                return DafnyErrorType.Forall;
            }
            else if (
                errorMessage.Contains(
                    "the calculation step between the previous line and this line could not be proved"
                )
            )
            {
                return DafnyErrorType.Calc;
            }
            else
            {
                return DafnyErrorType.Unknown;
            }
        }
    }

    class ErrorLocation
    {
        public string File { get; set; }
        public int Line { get; set; }
        public int Column { get; set; }

        public ErrorLocation() { }

        public List<ErrorLocation> FindLocationFromError(
            Uri uri,
            Program program,
            DafnyError error,
            bool multiple_location
        )
        {
            var errorLocations = new List<ErrorLocation>();
            switch (error.ErrorType)
            {
                case DafnyErrorType.Assertion:
                    errorLocations = AssignErrorLocation(program, uri, error, multiple_location);
                    break;
                case DafnyErrorType.Precondition:
                    errorLocations = AssignErrorLocation(program, uri, error, multiple_location);
                    break;
                case DafnyErrorType.Postcondition:
                    errorLocations = AssignAtEndOfBlock(program, uri, error, multiple_location);
                    break;
                case DafnyErrorType.LHSValue:
                    errorLocations = AssignErrorLocation(program, uri, error, multiple_location);
                    break;
                case DafnyErrorType.AssertBy:
                    errorLocations = AssignAtEndOfBlock(program, uri, error, multiple_location);
                    break;
                case DafnyErrorType.Forall:
                    errorLocations = AssignAtEndOfBlock(program, uri, error, multiple_location);
                    break;
                case DafnyErrorType.Calc:
                    errorLocations = AssignErrorLocation(program, uri, error, multiple_location);
                    break;
                default:
                    throw new ArgumentException("Invalid error type");
            }
            return errorLocations;
        }

        public static LList<INode> ExtractFindNodeChain(
            INode node,
            Uri uri,
            DafnyPosition position,
            LList<INode> parent,
            Func<INode, bool> predicate
        )
        {
            if (node.RangeToken.Uri != null)
            {
                if (node.RangeToken.Uri == uri)
                {
                    return ExtractedFindNodeChain(node, position, parent, predicate);
                }

                return null;
            }

            LList<INode> parent2 = new LList<INode>(node, parent);
            foreach (INode child in node.Children)
            {
                LList<INode> lList = ExtractFindNodeChain(child, uri, position, parent2, predicate);
                if (lList != null)
                {
                    return lList;
                }
            }

            return null;
        }

        public static LList<INode> ExtractedFindNodeChain(
            INode node,
            DafnyPosition position,
            LList<INode> parent,
            Func<INode, bool> predicate
        )
        {
            if (
                node.Tok is AutoGeneratedToken
                || (node.Tok != Token.NoToken && !node.RangeToken.ToDafnyRange().Contains(position))
            )
            {
                return null;
            }

            LList<INode> parent2 = new LList<INode>(node, parent);
            foreach (INode child in node.Children)
            {
                LList<INode> lList = ExtractedFindNodeChain(child, position, parent2, predicate);
                if (lList != null)
                {
                    return lList;
                }
            }

            if (node.Tok == Token.NoToken || !predicate(node))
            {
                return null;
            }

            return new LList<INode>(node, parent);
        }

        public List<ErrorLocation> GetErrorLocationsWithoutFindNode(
            BlockStmt blockStatement,
            IToken token
        )
        {
            var errorLocations = new List<ErrorLocation>();
            // check if the block statement contains a if statement
            foreach (var statement in blockStatement.Body)
            {
                if (statement is IfStmt ifStatement)
                {
                    var thenErrorLocation = new ErrorLocation
                    {
                        File = token.filename,
                        Line = ifStatement.Thn.EndToken.line,
                        Column = ifStatement.Thn.EndToken.col
                    };
                    errorLocations.Add(thenErrorLocation);

                    if (ifStatement.Els != null)
                    {
                        var elseErrorLocation = new ErrorLocation
                        {
                            File = token.filename,
                            Line = ifStatement.Els.EndToken.line,
                            Column = ifStatement.Els.EndToken.col
                        };
                        errorLocations.Add(elseErrorLocation);
                    }
                }
            }
            return errorLocations;
        }

        public List<ErrorLocation> GetErrorLocations(Program program, Uri uri, IToken token)
        {
            //TODO document this -1
            var errorLocations = new List<ErrorLocation>();
            var position = new DafnyPosition(token.line - 1, token.col);
            var listNode = ExtractFindNodeChain(
                program,
                uri,
                position,
                null,
                (INode node) => node is Statement
            );
            var node = listNode.Data;
            while (node != null)
            {
                if (node is BlockStmt blockStatement)
                {
                    break;
                }
                listNode = listNode.Next;
                node = listNode?.Data;
            }
            // check if the block statement contains a if statement
            errorLocations = GetErrorLocationsWithoutFindNode((BlockStmt)node, token);

            return errorLocations;
        }

        public List<ErrorLocation> AssignErrorLocation(
            Program program,
            Uri uri,
            DafnyError error,
            bool multiple_location
        )
        {
            var errorLocations = new List<ErrorLocation>();
            var token = error.SourceStatement.Tok;
            this.File = token.filename;
            this.Line = token.line;
            this.Column = token.col;
            if (multiple_location)
            {
                errorLocations = GetErrorLocations(program, uri, token);
            }
            return errorLocations;
        }

        public List<ErrorLocation> AssignAtEndOfBlock(
            Program program,
            Uri uri,
            DafnyError error,
            bool multiple_location
        )
        {
            var errorLocations = new List<ErrorLocation>();
            var token = error.SourceStatement.EndToken;
            this.File = token.filename;
            this.Line = token.line;
            this.Column = token.col;
            if (multiple_location)
            {
                var node = error.SourceStatement;
                BlockStmt blockStatement = null;

                if (node is IfStmt ifStatement)
                {
                    blockStatement = ifStatement.Thn as BlockStmt;
                    if (ifStatement.Els != null)
                    {
                        blockStatement = ifStatement.Els as BlockStmt;
                    }
                }
                else if (node is ForallStmt forallStatement)
                {
                    blockStatement = forallStatement.Body as BlockStmt;
                }
                else if (node is AssertStmt assertStatement)
                {
                    blockStatement = assertStatement.SubStatements as BlockStmt;
                }

                if (blockStatement != null)
                {
                    errorLocations = GetErrorLocationsWithoutFindNode(blockStatement, token);
                }
            }
            return errorLocations;
        }

        public void AssignAfterErrorLocation(DafnyError error)
        {
            var token = error.SourceStatement.Tok;
            this.File = token.filename;
            this.Line = token.line + 1;
            this.Column = token.col;
        }

        public override string ToString()
        {
            return $"{File}({Line},{Column})";
        }
    }

    class MainReturnValTest
    {
        public static Declaration FindMethodByName(Program program, string declarationName)
        {
            foreach (var module in program.Modules())
            {
                foreach (var decl in module.TopLevelDecls)
                {
                    if (decl is TopLevelDeclWithMembers c)
                    {
                        foreach (var member in c.Members)
                        {
                            if (
                                (member is Function f && f.Name == declarationName)
                                || (member is Method m && m.Name == declarationName)
                                || (member is Lemma l && l.Name == declarationName)
                            )
                            {
                                return member;
                            }
                        }
                    }
                }
            }
            return null; // Return null if the method is not found
        }

        public static DafnyError IdentifyPriorityError(
            Uri uri,
            Program program,
            Method method,
            List<DafnyError> errorMessages
        )
        {
            var error = FindMatchingError(method.Body, errorMessages);
            if (error != null)
            {
                return error;
            }

            return null;
        }

        public static DafnyError IdentifyPriorityError(Lemma lemma, List<DafnyError> errorMessages)
        {
            var error = FindMatchingError(lemma.Body, errorMessages);
            if (error != null)
            {
                return error;
            }

            return null;
        }

        private static DafnyError FindMatchingError(
            Statement statement,
            List<DafnyError> errorMessages
        )
        {
            foreach (var error in errorMessages)
            {
                if (error.SourceStatement.Tok.line == statement.Tok.line)
                {
                    return error;
                }

                foreach (var relatedError in error.RelatedErrors)
                {
                    if (relatedError.SourceStatement == statement)
                    {
                        return relatedError;
                    }
                }
            }

            if (statement is BlockStmt blockStmt)
            {
                foreach (var subStatement in blockStmt.Body)
                {
                    var error = FindMatchingError(subStatement, errorMessages);
                    if (error != null)
                    {
                        return error;
                    }
                }
            }
            else if (statement is IfStmt ifStmt)
            {
                // Check if the error is within the range of the 'else' token
                var thenError = FindMatchingError(ifStmt.Thn, errorMessages);
                if (thenError != null)
                {
                    return thenError;
                }

                if (ifStmt.Els != null)
                {
                    var elseError = FindMatchingError(ifStmt.Els, errorMessages);
                    if (elseError != null)
                    {
                        return elseError;
                    }
                }
                var elseToken = ifStmt.OwnedTokens.FirstOrDefault(t => t.val == "else");
                if (elseToken != null)
                {
                    foreach (var error in errorMessages)
                    {
                        if (
                            error.Line == elseToken.line
                            && error.Column >= elseToken.col
                            && error.Column <= elseToken.col + elseToken.val.Length
                        )
                        {
                            error.SourceStatement = ifStmt.Els;
                            return error;
                        }
                    }
                }
                //TODO same for if statement?
            }
            else if (statement is MatchStmt matchStmt)
            {
                foreach (var matchCase in matchStmt.Cases)
                {
                    foreach (var subStatement in matchCase.Body)
                    {
                        var caseError = FindMatchingError(subStatement, errorMessages);
                        if (caseError != null)
                        {
                            return caseError;
                        }
                    }
                }
            }
            else if (statement is NestedMatchStmt nestedMatchStmt)
            {
                foreach (var matchCase in nestedMatchStmt.Cases)
                {
                    foreach (var subStatement in matchCase.Body)
                    {
                        var caseError = FindMatchingError(subStatement, errorMessages);
                        if (caseError != null)
                        {
                            return caseError;
                        }
                    }
                }
            }
            else if (statement is ForallStmt forallStmt)
            {
                var error = FindMatchingError(forallStmt.Body, errorMessages);
                if (error != null)
                {
                    return error;
                }
            }
            else if (statement is WhileStmt whileStmt)
            {
                var error = FindMatchingError(whileStmt.Body, errorMessages);
                if (error != null)
                {
                    return error;
                }
            }
            else if (statement is AssertStmt assertStmt)
            {
                foreach (var substatement in assertStmt.SubStatements)
                {
                    var error = FindMatchingError(substatement, errorMessages);
                    if (error != null)
                    {
                        return error;
                    }
                }
            }

            return null;
        }

        public static List<string> InsertPlaceholderAtLine(
            List<string> lines,
            int line,
            string placeholder
        )
        {
            lines.Insert(line - 1, placeholder);
            // File.WriteAllLines(filename, lines);
            return lines;
        }

        public static Dictionary<Uri, string> AddFilesToFs(
            string methodFile,
            string additionalFilesDir = "",
            string blacklistFile = ""
        )
        {
            var fileDictionary = new Dictionary<Uri, string>();

            var fileContent = File.ReadAllText(methodFile);
            var baseMethodUri = new Uri("transcript:///" + methodFile);
            fileDictionary.Add(baseMethodUri, fileContent);

            // If additionalFilesDir is not empty, add additional files to the dictionary
            if (!string.IsNullOrEmpty(additionalFilesDir))
            {
                string searchPattern = "*.dfy";
                string directoryPath = additionalFilesDir;
                SearchOption searchOption = SearchOption.AllDirectories;

                if (additionalFilesDir.Contains("**"))
                {
                    // If '**' is present, adjust the directory path and set the search option to AllDirectories
                    directoryPath = additionalFilesDir.Substring(
                        0,
                        additionalFilesDir.IndexOf("**")
                    );
                }
                foreach (
                    string fileInclude in Directory.EnumerateFiles(
                        directoryPath,
                        searchPattern,
                        searchOption
                    )
                )
                {
                    // If blacklistFile is not empty and the current file matches it, skip this file
                    if (!string.IsNullOrEmpty(blacklistFile) && fileInclude.Contains(blacklistFile))
                    {
                        continue;
                    }

                    fileContent = File.ReadAllText(fileInclude);
                    var fileUri = new Uri("transcript:///" + fileInclude);

                    if (!fileDictionary.ContainsKey(fileUri))
                    {
                        fileDictionary.Add(fileUri, fileContent);
                    }
                }
            }

            return fileDictionary;
        }

        static int Main(string[] args)
        {
            TextWriter output = Console.Error;
            DafnyOptions options = DafnyOptions.Create(output);
            BatchErrorReporter errorReporter = new BatchErrorReporter(options);
            var methodFile = "";
            var methodName = "";
            bool multiple_location = false;
            var additionnalInclude = "";
            var blacklistedFile = "";
            if (args.Length < 2)
            {
                Console.WriteLine(
                    "Usage: Program <method_file> <method_name> [multiple_location] [additional_include] [blacklisted_file]"
                );
                return 0;
            }
            else
            {
                methodFile = args[0];
                methodName = args[1];
                multiple_location = args.Length > 2 ? bool.Parse(args[2]) : false; // default value is false
                additionnalInclude = args.Length > 3 ? args[3] : null; // default value is null
                blacklistedFile = args.Length > 4 ? args[4] : null; // default value is null
            }

            string input;
            input = Console.In.ReadToEnd();
            if (!Path.IsPathRooted(methodFile))
            {
                methodFile = Path.GetFullPath(methodFile);
            }

            // Create a URI from the file name
            var uri = new Uri("transcript:///" + methodFile);

            // Initialize an error reporter to report errors to the console
            var reporter = new ConsoleErrorReporter(options);

            var filesDict = AddFilesToFs(methodFile, additionnalInclude, blacklistedFile);

            var files = new List<DafnyFile>();
            var fs = new InMemoryFileSystem(filesDict);
            foreach (var dafnyElement in filesDict)
            {
                var dafnyFile = DafnyFile.CreateAndValidate(
                    reporter,
                    fs,
                    reporter.Options,
                    dafnyElement.Key,
                    Token.NoToken
                );
                files.Add(dafnyFile);
            }
            var program = new ProgramParser().ParseFiles(
                methodFile,
                files,
                reporter,
                CancellationToken.None
            );

            var resolver = new ProgramResolver(program);

            resolver.Resolve(CancellationToken.None);

            var success = !reporter.HasErrors;

            if (!success)
            {
                Console.WriteLine("Error reporter: " + reporter.ErrorCount);
                foreach (var message in reporter.AllMessages)
                {
                    throw new Exception("Error parsing or reporting method file: " + message);
                }
                return 1;
            }

            var declaration = FindMethodByName(program, methodName);
            if (declaration == null)
            {
                throw new Exception("Method not found: " + methodName);
            }

            var errors = ErrorParser.ParseErrors(input);
            if (errors.Count == 0)
            {
                throw new Exception("No errors found in input: {input}");
            }
            else
            {
                foreach (var error_dfy in errors)
                {
                    error_dfy.findStatementNode(program, uri);
                    if (error_dfy.RelatedErrors.Count > 0)
                    {
                        foreach (var relatedError in error_dfy.RelatedErrors)
                        {
                            relatedError.findStatementNode(program, uri);
                        }
                    }
                }
            }
            DafnyError error = null;
            if (declaration is Method method)
            {
                error = IdentifyPriorityError(uri, program, method, errors);
            }
            else if (declaration is Lemma lemma)
            {
                error = IdentifyPriorityError(lemma, errors);
            }
            else
            {
                throw new Exception("declaration not supported: " + declaration.GetType());
            }

            if (error == null)
            {
                throw new Exception("No error found matching!!");
            }

            var errorLocation = new ErrorLocation();
            var potential_locations = errorLocation.FindLocationFromError(
                uri,
                program,
                error,
                multiple_location
            );

            potential_locations.Add(errorLocation);
            potential_locations = potential_locations.OrderBy(location => location.Line).ToList();

            // get method lines and insert placeholder
            var method_start_line = declaration.tok.line;
            var method_end_line = declaration.EndToken.line;
            var file_to_modify = declaration.tok.Filepath;

            var file_lines = File.ReadAllLines(file_to_modify).ToList();
            int offset = 0;
            foreach (var location in potential_locations)
            {
                file_lines = InsertPlaceholderAtLine(
                    file_lines,
                    location.Line + offset,
                    "<assertion> Insert assertion here </assertion>"
                );
                offset++;
            }

            method_end_line += offset;

            // Extract the method
            var method_lines = file_lines.ToArray()[(method_start_line - 1)..(method_end_line)];
            Console.WriteLine(string.Join("\n", method_lines));

            return 0;
        }
    }
}
