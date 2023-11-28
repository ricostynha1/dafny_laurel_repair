import csv


def adjust_microseconds(time_str, desired_precision):
    seconds, microseconds = time_str.split(".")

    rounded_microseconds = str(round(float(f"0.{microseconds}"), desired_precision))[2:]
    padded_microseconds = rounded_microseconds.ljust(desired_precision, "0")

    adjusted_time_str = f"{seconds}.{padded_microseconds}"

    return adjusted_time_str


def read_pruning_result(csv_file_path):
    csv_data = []
    with open(csv_file_path, newline="") as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            csv_data.append(row)
        return csv_data


def write_csv_header(csv_file_path):
    header = [
        "Index",
        "File",
        "Method",
        "Assertion",
        "Time difference",
        "File new method",
        "New method time",
        "New method result",
        "Old method time",
    ]
    csv_file = open(csv_file_path, "a", newline="")
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(header)
    return csv_writer
