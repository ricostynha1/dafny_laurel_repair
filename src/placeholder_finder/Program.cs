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
    public class DafnyError
    {
        public string File { get; set; }
        public int Line { get; set; }
        public int Column { get; set; }
        public string ErrorMessage { get; set; }
        public string LineContent { get; set; }
        public List<DafnyError> RelatedErrors { get; set; } = new List<DafnyError>();

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
                        ErrorMessage = errorMessage
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
    }

    class ErrorMessageDivider
    {
        public static List<string> DivideErrorMessages(string errorMessages)
        {
            var errors = new List<string>();
            var error = "";
            foreach (var line in errorMessages.Split('\n'))
            {
                if (
                    line.Contains("Dafny program verifier finished with")
                    || line.Contains("Dafny program verifier failed with")
                )
                {
                    if (error != "")
                    {
                        errors.Add(error);
                    }
                    error = "";
                }
                error += line + "\n";
            }
            return errors;
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

        public static (Statement, string) IdentifyPriorityError(
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
                        return (statement, error.ErrorMessage);
                    }

                    foreach (var relatedError in error.RelatedErrors)
                    {
                        if (relatedError.LineContent == statement.ToString())
                        {
                            return (statement, relatedError.ErrorMessage);
                        }
                    }
                }
            }
            return (null, null);
        }

        public static (Statement, string) IdentifyPriorityError(
            Lemma lemma,
            List<DafnyError> errorMessages
        )
        {
            foreach (var statement in lemma.Body.Body)
            {
                foreach (var error in errorMessages)
                {
                    if (error.LineContent == statement.ToString())
                    {
                        return (statement, error.ErrorMessage);
                    }

                    foreach (var relatedError in error.RelatedErrors)
                    {
                        if (relatedError.LineContent == statement.ToString())
                        {
                            return (statement, relatedError.ErrorMessage);
                        }
                    }
                }
            }
            return (null, null);
        }

        public static (Statement, string) IdentifyPriorityError(
            Lemma lemma,
            List<string> errorMessages
        )
        {
            foreach (var statement in lemma.Body.Body)
            {
                if (errorMessages.Contains(statement.ToString()))
                {
                    return (statement, statement.ToString());
                }
            }
            return (null, null);
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
            foreach (var error in errors)
            {
                Console.WriteLine(error);
            }
            if (!Path.IsPathRooted(methodFile))
            {
                methodFile = Path.GetFullPath(methodFile);
            }
            // Uri uri = new Uri(methodFile);
            // Console.WriteLine("URI: " + uri);

            // Create a URI from the file name
            var uri = new Uri("transcript:///" + methodFile);

            // Initialize an error reporter to report errors to the console
            var reporter = new ConsoleErrorReporter(options);

            var methodInput = File.ReadAllText(methodFile);

            // Create an in-memory file system with the source code associated with the URI

            // var fs = new InMemoryFileSystem(ImmutableDictionary<Uri, string>.Empty.Add(uri, methodInput));

            // add all the files from src/**/*.dfy


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

            // Handle the Dafny file using the in-memory file system and the reporter
            // var file = DafnyFile.CreateAndValidate(reporter, fs, reporter.Options, uri, Token.NoToken);
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
            // Parse the Dafny file and get a program representation
            var program = new ProgramParser().ParseFiles(
                methodFile,
                files,
                reporter,
                CancellationToken.None
            );

            // Check if there were any errors reported
            var success = !reporter.HasErrors;

            // If parsing was successful, assign the program to the class-level variable
            // if (success) {
            //     dafnyProgram = program;
            // }
            if (!success)
            {
                Console.WriteLine("Error reporter: " + reporter.ErrorCount);
                foreach (var message in reporter.AllMessages)
                {
                    Console.WriteLine(message);
                }
                return 1;
            }

            // open the method file

            // var program = new ProgramParser().Parse(methodInput, uri, errorReporter);
            var resolver = new ProgramResolver(program);

            resolver.Resolve(CancellationToken.None);

            Console.WriteLine("Error reporter: " + errorReporter.ErrorCount);
            foreach (var message in errorReporter.AllMessages)
            {
                Console.WriteLine(message);
            }

            var declaration = FindMethodByName(program, methodName);
            if (declaration is Method method)
            {
                var error = IdentifyPriorityError(method, errors);
            }
            else if (declaration is Lemma lemma)
            {
                var error = IdentifyPriorityError(lemma, errors);
            }
            else
            {
                throw new Exception("declaration not supported");
            }

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
