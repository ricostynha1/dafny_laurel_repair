using Microsoft.Dafny;
using System.Text;
using System.Threading;
using System.Diagnostics.Contracts;
using System;
using System.IO;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Text.Json;

namespace tokenizer
{



    public class ProgramScanner
    {
        public static Scanner SetupScanner(string s /*!*/, Uri uri /*!*/,
          ErrorReporter errorReporter /*!*/)
        {
            Contract.Requires(s != null);
            Contract.Requires(uri != null);
            System.Runtime.CompilerServices.RuntimeHelpers.RunClassConstructor(typeof(ParseErrors).TypeHandle);
            System.Runtime.CompilerServices.RuntimeHelpers.RunClassConstructor(typeof(ResolutionErrors).TypeHandle);
            /* System.Runtime.CompilerServices.RuntimeHelpers.RunClassConstructor(typeof(ParseErrors).TypeHandle); */
            /* System.Runtime.CompilerServices.RuntimeHelpers.RunClassConstructor(typeof(ResolutionErrors).TypeHandle); */
            byte[] /*!*/ buffer = cce.NonNull(Encoding.Default.GetBytes(s));
            var ms = new MemoryStream(buffer, false);
            var firstToken = new Token
            {
                Uri = uri
            };

            var errors = new Errors(errorReporter);
            var scanner = new Scanner(ms, errors, uri, firstToken: firstToken);
            return scanner;

        }
    }
    class MainReturnValTest
    {
        static int Main(string[] args)
        {

            // Read from a file passed as argument or stdin if no argument is passed
            TextWriter output = Console.Out;
            DafnyOptions options = DafnyOptions.Create(output);
            BatchErrorReporter errorReporter = new BatchErrorReporter(options);
            string filePath = "/placeholder.dfy";
            string input;
            if (args.Length > 0)
            {
                filePath = args[0];
                input = File.ReadAllText(filePath);
            }
            else
            {
                input = Console.In.ReadToEnd();
            }
            Uri uri = new Uri(filePath);

            var scanner = ProgramScanner.SetupScanner(input, uri, errorReporter);

            List<List<Tuple<string, string>>> tokens = new List<List<Tuple<string, string>>>();
            List<Tuple<string, string>> currentList = new List<Tuple<string, string>>();

            Token token;
            int previousLine = 1;

            do
            {
                token = scanner.Peek();
                // a tuple of the token kind and the token text
                // if it's a different line than the previous create a new list and add the current list to the list of lists
                // add the tuple to the list
                if (token.line != previousLine)
                {
                    tokens.Add(currentList);
                    currentList = new List<Tuple<string, string>>
                    {
                        new Tuple<string, string>(token.kind.ToString(), token.val)
                    };
                    previousLine = token.line;
                }
                else
                {
                    currentList.Add(new Tuple<string, string>(token.kind.ToString(), token.val));
                }
            }
            while (token.kind != Parser._EOF);
            tokens.Add(currentList);
            string json = JsonSerializer.Serialize(tokens);

            if (args.Length > 0)
            {
                File.WriteAllText(filePath + "_tokens", json);
            }
            else
            {
                Console.WriteLine(json);
            }
            return 0;
        }
    }
}
