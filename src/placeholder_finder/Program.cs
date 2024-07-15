using System;
using System.Collections.Generic;
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
            Uri uri = new Uri(methodFile);

            var program = new ProgramParser().Parse(input, uri, errorReporter);
            var resolver = new ProgramResolver(program);

            resolver.Resolve(CancellationToken.None);

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
