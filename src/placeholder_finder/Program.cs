using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Diagnostics.Contracts;
using System.IO;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.Dafny;

namespace placeholder
{
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
                        if ((member is Function f && f.Name == declarationName) ||
                        (member is Method m && m.Name == declarationName) ||
                        (member is Lemma l && l.Name == declarationName))
                    {
                        return member;
                    }
                        }
                    }
                }
            }
            return null; // Return null if the method is not found
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
            foreach (string fileInclude in Directory.EnumerateFiles("/usr/local/home/eric/dafny_repos/Dafny-VMC/src", "*.dfy", SearchOption.AllDirectories))
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
                var dafnyFile = DafnyFile.CreateAndValidate(reporter, fs, reporter.Options, dafnyElement.Key, Token.NoToken);
                files.Add(dafnyFile);
            }
            // Parse the Dafny file and get a program representation
            var program = new ProgramParser().ParseFiles(methodFile, files,
                reporter, CancellationToken.None);

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

            var method = FindMethodByName(program, methodName);
            Console.WriteLine(method);

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
