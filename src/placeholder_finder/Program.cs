using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Diagnostics.Contracts;
using System.IO;
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
                // Add cases for other error types
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
            Method method,
            List<DafnyError> errorMessages
        )
        {
            foreach (var statement in method.Body.Body)
            {
                foreach (var error in errorMessages)
                {
                    if (error.LineContent == statement.ToString())
                    {
                        error.SourceStatement = statement;
                        return error;
                    }

                    foreach (var relatedError in error.RelatedErrors)
                    {
                        if (relatedError.LineContent == statement.ToString())
                        {
                            error.SourceStatement = statement;
                            return error;
                        }
                    }
                }
            }
            return null;
        }

        public static DafnyError IdentifyPriorityError(Lemma lemma, List<DafnyError> errorMessages)
        {
            foreach (var statement in lemma.Body.Body)
            {
                foreach (var error in errorMessages)
                {
                    if (error.LineContent == statement.ToString())
                    {
                        error.SourceStatement = statement;
                        return error;
                    }

                    foreach (var relatedError in error.RelatedErrors)
                    {
                        if (relatedError.LineContent == statement.ToString())
                        {
                            error.SourceStatement = statement;
                            return error;
                        }
                    }
                }
            }
            return null;
        }

        static int Main(string[] args)
        {
            TextWriter output = Console.Out;
            DafnyOptions options = DafnyOptions.Create(output);
            BatchErrorReporter errorReporter = new BatchErrorReporter(options);
            if (args.Length != 2)
            {
                Console.WriteLine("Usage: Program <method_file> <method_name>");
                return 0;
            }

            string methodFile = args[0];
            string methodName = args[1];
            string input;
            input = Console.In.ReadToEnd();
            var errors = ErrorParser.ParseErrors(input);
            foreach (var dafnyError in errors)
            {
                Console.WriteLine(dafnyError);
            }
            if (!Path.IsPathRooted(methodFile))
            {
                methodFile = Path.GetFullPath(methodFile);
            }

            // Create a URI from the file name
            var uri = new Uri("transcript:///" + methodFile);

            // Initialize an error reporter to report errors to the console
            var reporter = new ConsoleErrorReporter(options);

            var methodInput = File.ReadAllText(methodFile);

            // TODO this is a special case for Dafny-VMC --library flag (it should not be needed for the rest)
            var ImmutableDictionary = new Dictionary<Uri, string>();
            foreach (
                string fileInclude in Directory.EnumerateFiles(
                    "/usr/local/home/eric/dafny_repos/Dafny-VMC/src",
                    "*.dfy",
                    SearchOption.AllDirectories
                )
            )
            {
                // everything except Reals.dfy
                if (fileInclude.Contains("Reals.dfy"))
                {
                    continue;
                }
                var fileContent = File.ReadAllText(fileInclude);
                var fileUri = new Uri("transcript:///" + fileInclude);
                ImmutableDictionary.Add(fileUri, fileContent);
            }
            var fs = new InMemoryFileSystem(ImmutableDictionary.ToImmutableDictionary());

            var files = new List<DafnyFile>();
            foreach (var dafnyElement in ImmutableDictionary)
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

            var success = !reporter.HasErrors;

            if (!success)
            {
                Console.WriteLine("Error reporter: " + reporter.ErrorCount);
                foreach (var message in reporter.AllMessages)
                {
                    throw new Exception("Error parsing method file: " + message);
                }
                return 1;
            }

            var resolver = new ProgramResolver(program);

            resolver.Resolve(CancellationToken.None);

            Console.WriteLine("Error reporter: " + errorReporter.ErrorCount);
            foreach (var message in errorReporter.AllMessages)
            {
                Console.WriteLine(message);
            }

            var declaration = FindMethodByName(program, methodName);

            DafnyError error = null;
            // TODO put this in a function taking a declaration method
            if (declaration is Method method)
            {
                error = IdentifyPriorityError(method, errors);
            }
            else if (declaration is Lemma lemma)
            {
                error = IdentifyPriorityError(lemma, errors);
            }
            else
            {
                throw new Exception("declaration not supported");
            }

            var errorLocation = new ErrorLocation();
            errorLocation.FindLocationFromError(error);
            Console.WriteLine(errorLocation);

            /* var position = new DafnyPosition(6, 10); */
            /**/
            /* var node_assert = program.FindNode<Node>(uri, position); */
            // var parent = (Node)program.FindNodeChain(position, node => node.Children is Node)?.Data;
            // var parent = node_assert.Parent;

            // Here for finding a function https://github.com/dafny-lang/dafny/blob/master/Source/DafnyCore/Generic/Util.cs#L491

            // static Graph<Function> BuildFunctionCallGraph(Dafny.Program program)

            Console.WriteLine("DONE");
            return 0;
        }
    }
}
