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
            var listNode = program.FindNodeChain(position, (INode node) => node is Statement);
            var node_assert = program.FindNode<Statement>(uri, position);
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

        public void FindLocationFromError(DafnyError error)
        {
            switch (error.ErrorType)
            {
                case DafnyErrorType.Assertion:
                    AssignErrorLocation(error);
                    break;
                case DafnyErrorType.Precondition:
                    AssignErrorLocation(error);
                    break;
                case DafnyErrorType.Postcondition:
                    AssignAtEndOfBlock(error);
                    break;
                case DafnyErrorType.LHSValue:
                    AssignErrorLocation(error);
                    break;
                case DafnyErrorType.AssertBy:
                    AssignAtEndOfBlock(error);
                    break;
                case DafnyErrorType.Forall:
                    AssignAtEndOfBlock(error);
                    break;
                case DafnyErrorType.Calc:
                    AssignErrorLocation(error);
                    break;
                default:
                    throw new ArgumentException("Invalid error type");
            }
        }

        public void AssignErrorLocation(DafnyError error)
        {
            var token = error.SourceStatement.Tok;
            this.File = token.filename;
            this.Line = token.line;
            this.Column = token.col;
        }

        public void AssignAtEndOfBlock(DafnyError error)
        {
            var token = error.SourceStatement.EndToken;
            this.File = token.filename;
            this.Line = token.line;
            this.Column = token.col;
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

        public static string[] InsertPlaceholderAtLine(
            string filename,
            int line,
            string placeholder
        )
        {
            var lines = File.ReadAllLines(filename).ToList();
            lines.Insert(line - 1, placeholder);
            // File.WriteAllLines(filename, lines);
            return lines.ToArray();
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
            var additionnalInclude = "";
            var blacklistedFile = "";
            if (args.Length < 2)
            {
                Console.WriteLine(
                    "Usage: Program <method_file> <method_name> [optional_third_arg]"
                );
                return 0;
            }
            else if (args.Length == 4)
            {
                methodFile = args[0];
                methodName = args[1];
                additionnalInclude = args[2];
                blacklistedFile = args[3];
            }
            else if (args.Length == 3)
            {
                methodFile = args[0];
                methodName = args[1];
                additionnalInclude = args[2];
            }
            else
            {
                methodFile = args[0];
                methodName = args[1];
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
            errorLocation.FindLocationFromError(error);

            // get method lines and insert placeholder
            var method_start_line = declaration.tok.line;
            var method_end_line = declaration.EndToken.line;
            var file_to_modify = declaration.tok.Filepath;

            var modified_files = InsertPlaceholderAtLine(
                file_to_modify,
                errorLocation.Line,
                "<assertion> Insert assertion here </assertion>"
            );

            // Extract the method
            var method_lines = modified_files[(method_start_line - 1)..(method_end_line + 1)];
            // Write method lines to stdout
            Console.WriteLine(string.Join("\n", method_lines));

            /* var position = new DafnyPosition(6, 10); */
            /**/
            /* var node_assert = program.FindNode<Node>(uri, position); */
            // var parent = (Node)program.FindNodeChain(position, node => node.Children is Node)?.Data;
            // var parent = node_assert.Parent;

            // Here for finding a function https://github.com/dafny-lang/dafny/blob/master/Source/DafnyCore/Generic/Util.cs#L491

            // static Graph<Function> BuildFunctionCallGraph(Dafny.Program program)

            return 0;
        }
    }
}
