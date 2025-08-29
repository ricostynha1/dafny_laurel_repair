import logging
import subprocess
import os
# ricostynha modified dotnet version
# before PLACEHOLDER_CSHARP_PATH = "placeholder_finder/bin/Debug/net6.0/placeholder_finder"
# after
PLACEHOLDER_LAUREL_CSHARP_PATH = "placeholder_finder/bin/Debug/net6.0/placeholder_finder"
PLACEHOLDER_LAUREL_BETTER_CSHARP_PATH = "placeholder_finder_better/bin/Debug/net6.0/placeholder_finder_laurel_better"

logger = logging.getLogger(__name__)


def call_placeholder_finder(
    error_message,
    method_file,
    method_name,
    use_laurel_better=False,
    optional_files=None,
    blacklisted_file=None,
    multiple_locations=False,
):
    if(use_laurel_better):
        placeholder_path_exec = PLACEHOLDER_LAUREL_BETTER_CSHARP_PATH 
    else:
        placeholder_path_exec = PLACEHOLDER_LAUREL_CSHARP_PATH 

    command = [
        os.path.join(os.path.dirname(__file__), placeholder_path_exec),
        method_file,
        method_name,
        str(multiple_locations),
    ]
    if optional_files:
        if not os.path.isabs(optional_files):
            optional_files = os.path.abspath(os.path.normpath(optional_files))
        command.append(optional_files)
    if blacklisted_file:
        command.append(blacklisted_file)
    try:
        result = subprocess.run(
            command, input=error_message, capture_output=True, text=True, check=True
        )

    
    except subprocess.CalledProcessError as e:
        # ricostynha modified error logger to be easier to use in following scripts
        # before
        #logger.error(f"Error in call_placeholder_finder: {str(e.stderr)}")
        #logger.error(
        #    f"Arguments were: method_file={method_file}, method_name={method_name}, optional_files={optional_files}, blacklisted_file={blacklisted_file}"
        #)
        #return ""
        # after 
        error = e.stdout
        error += f"Error in call_placeholder_finder: {str(e.stderr)}"
        error +=  f"Arguments were: method_file={method_file}, method_name={method_name}, optional_files={optional_files}, blacklisted_file={blacklisted_file}"
        print(error)
        return "", error   

    except Exception as e:
        # general fallback for any other exception
        error = f"Unexpected error: {str(e)}"
        error +=  f"Arguments were: method_file={method_file}, method_name={method_name}, optional_files={optional_files}, blacklisted_file={blacklisted_file}"
        print(error)
        return "", error
    

    output = result.stdout.strip()
    #before
    #print(output)
    #return output
    #after
    #print(f"Output is {output}")
    return output, ""

