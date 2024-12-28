import json
from termcolor import colored as colored_raw


def colored(*args, **kwargs):
    return colored_raw(*args, **kwargs, force_color=True)


from corexploration.models.mss import mss, data


def token_comp(t1, t2):
    # if any is not a token, return 0
    if not isinstance(t1, data.PyToken) or not isinstance(t2, data.PyToken):
        return 0
    # if they are not the same type, return 0
    if t1.token_type == "HOLE" or t2.token_type == "HOLE":
        return 0
    if t1.token_type != t2.token_type:
        return 0
    # if they are not variable names, compare the strings for equality
    if t1.token_type != "NAME" and t1.token_type != "STRING":
        return 1 if t1.string == t2.string else 0
    # otherwise, compare the strings for similarity
    mss_res = mss.MostSimilarSubsequence(t1.string, t2.string, mss.id_comp)
    sim = mss_res.similarity("mean")
    if sim == 0:
        # hacky af
        sim = 1e-6
    return sim


def str_tokens(tokens, color=False):
    def print_token(tk):
        if not color:
            return tk[1]
        if tk[0] == "KEYWORD":
            return colored(tk[1], "light_magenta")
        if tk[0] == "HOLE":
            return colored(tk[1], "dark_grey")
        else:
            return tk[1]

    return " ".join(print_token(tok) for tok in tokens)


def str_lines(lines, color=False):
    def print_line(line):
        if line == mss.HOLE:
            return colored("<line>", "dark_grey")
        return str_tokens(line, color)

    return "\n".join(print_line(line) for line in lines)


color_seq = {
    "reset": "\033[0m",
    "red": "\033[31m",
    "green": "\033[32m",
    "orange": "\033[33m",
    "blue": "\033[34m",
    "purple": "\033[35m",
    "cyan": "\033[36m",
}


def print_color(color, s, end="\n"):
    print(color_seq[color] + s + "\033[0m", end=end)


def color_str(s, color):
    return color_seq[color] + s + "\033[0m"


def diff_line(ts, ks, idx):
    # print_color("purple", f"~ {str_tokens(ts)}")
    # print_color("cyan", f"~ {str_tokens(ks)}")
    mss_res = mss.MostSimilarSubsequence(ts, ks, mss.token_comp)
    s_ids, k_ids = mss_res.s_sub, mss_res.t_sub
    exact_s, exact_k = [], []
    for i, j in zip(s_ids, k_ids):
        if ts[i] == ks[j]:
            exact_s.append(i)
            exact_k.append(j)

    def t_color(i):
        if i in exact_s:
            return colored(ts[i][1], "dark_grey")
        elif i in s_ids:
            return colored(ts[i][1], "light_grey")
        else:
            return colored(ts[i][1], "light_red")

    def k_color(i):
        if i in exact_k:
            return colored(ks[i][1], "dark_grey")
        elif i in k_ids:
            return colored(ks[i][1], "light_grey")
        else:
            return colored(ks[i][1], "light_green")

    print(colored(f"{idx: <2}", "white", "on_light_red"), end="")
    print(" ".join(t_color(i) for i in range(len(ts))))
    print(colored(f"{idx: <2}", "black", "on_light_green"), end="")
    print(" ".join(k_color(i) for i in range(len(ks))))
    # print(f"{color_str(str(idx), 'green')} { ' '.join(k_color(i) for i in range(len(ks)))}")


def mss_diff(sgg1, sgg2):
    mss_res = mss.MostSimilarSubsequence(sgg1, sgg2, mss.line_comp)
    mss_len, sim, s1_ids, s2_ids = (
        mss_res.mss(),
        mss_res.similarity("mean"),
        mss_res.s_sub,
        mss_res.t_sub,
    )
    i, j = 0, 0
    # TODO: this is hardcoded for this particular flavor of the similarity
    # we need to change this
    print(f"sim: {sim:.4f} mss: {mss_len:.4f}")
    for ai, (m_i, m_j) in enumerate(zip(s1_ids, s2_ids)):
        while i < m_i:
            print_color("red", f"< {str_tokens(sgg1[i])}")
            i += 1
        while j < m_j:
            print_color("green", f"> {str_tokens(sgg2[j])}")
            j += 1
        if sgg1[i] == sgg2[j]:
            print(f"  {str_tokens(sgg1[i])}")
        else:
            l1, l2 = sgg1[i], sgg2[j]
            diff_line(l1, l2, m_i)
        i = m_i + 1
        j = m_j + 1
    while i < len(sgg1):
        print_color("red", f"< {str_tokens(sgg1[i])}")
        i += 1
    while j < len(sgg2):
        print_color("green", f"> {str_tokens(sgg2[j])}")
        j += 1


def str_line(line, color):
    # return the string representation of a line
    # respecting the positions of the tokens in the line
    prev_col = 0
    res = []
    for tok in line:
        if tok is mss.HOLE:
            hole_str = " <__> "
            if color:
                hole_str = colored(hole_str, "dark_grey")
            res.append(hole_str)
            continue
        _, col = tok.start
        col_offset = col - prev_col
        if col_offset > 0:
            res.append(" " * col_offset)
        tok_str = tok.string
        if tok.token_type == "KEYWORD" and color:
            tok_str = colored(tok_str, "light_magenta")
        if tok.token_type == "COMMENT" and color:
            tok_str = colored(tok_str, "dark_grey")
        res.append(tok_str)
        prev_col = tok.end[1]
    return "".join(res)


def get_leading_whitespace(str):
    return len(str) - len(str.lstrip())


def str_line_ugly(line, color):
    if not line:
        return ""
    # first find a non-hole token and extract the whole line
    # find the leading whitespace and save it
    indent = None
    for tok in line:
        if tok is not mss.HOLE:
            indent = get_leading_whitespace(tok.line)
            break
    # if there are no non-hole tokens, then just return the line hole string
    if indent is None:
        str_line = " ..."
        if color:
            str_line = colored(str_line, "white")
        return str_line
    # # otherwise, get the tokens, and make a string with the leading whitespace
    # res = []
    # for tok in line:
    #     if tok is mss.HOLE:
    #         hole_str = "..."
    #         if color:
    #             hole_str = colored(hole_str, "light_grey")
    #         res.append(hole_str)
    #     else:
    #         tok_str = tok.string
    #         if tok.token_type == "KEYWORD" and color:
    #             tok_str = colored(tok_str, "light_magenta")
    #         if tok.token_type == "COMMENT" and color:
    #             tok_str = colored(tok_str, "light_grey")
    #         res.append(tok_str)
    # return " " * indent + " ".join(res)
    res = " " * indent
    prev_token = mss.HOLE
    for tok in line:
        # if both the current token and the previous token are not holes
        # compare the end of the previous token with the start of the current token
        # and add the necessary whitespace
        if tok is not mss.HOLE and prev_token is not mss.HOLE:
            col_offset = tok.start[1] - prev_token.end[1]
            res += " " * col_offset
        # else, add one space
        else:
            res += " "
        # if the token is a hole, add the hole string
        if tok is mss.HOLE:
            tok_str = "..."
            if color:
                tok_str = colored(tok_str, "white")
            res += tok_str
        # otherwise, add the token string
        else:
            tok_str = tok.string
            if tok.token_type == "KEYWORD" and color:
                tok_str = colored(tok_str, "light_magenta")
            if tok.token_type == "COMMENT" and color:
                tok_str = colored(tok_str, "white")
            res += tok_str
        prev_token = tok
    return res


def diff_line_new(l1, l2):
    comp = mss.mss_comp_aux(token_comp)
    mss_res = mss.MostSimilarSubsequence(l1, l2, comp)
    l1_ids, l2_ids = mss_res.s_sub, mss_res.t_sub
    l1_exact, l2_exact = [], []
    for i, j in zip(l1_ids, l2_ids):
        ij_sim = comp(l1[i], l2[j])
        if ij_sim == 1:
            l1_exact.append(i)
            l2_exact.append(j)
    # p_match_colors = ["light_blue", "light_magenta", "cyan"]
    p_match_colors = ["blue", "magenta", "cyan"]
    l1_res, l2_res = [], []
    prev_col = 0
    curr_p_match = 0
    for i, tok in enumerate(l1):
        _, col = tok.start
        col_offset = col - prev_col
        if col_offset > 0:
            l1_res.append(" " * col_offset)
        if i in l1_exact:
            l1_res.append(colored(tok.string, "white"))
        elif i in l1_ids:
            color = p_match_colors[curr_p_match]
            l1_res.append(colored(tok.string, color))
            curr_p_match = (curr_p_match + 1) % len(p_match_colors)
        else:
            l1_res.append(colored(tok.string, "red"))
        prev_col = tok.end[1]
    prev_col = 0
    curr_p_match = 0
    for i, tok in enumerate(l2):
        _, col = tok.start
        col_offset = col - prev_col
        if col_offset > 0:
            l2_res.append(" " * col_offset)
        if i in l2_exact:
            l2_res.append(colored(tok.string, "white"))
        elif i in l2_ids:
            color = p_match_colors[curr_p_match]
            l2_res.append(colored(tok.string, color))
            curr_p_match = (curr_p_match + 1) % len(p_match_colors)
        else:
            l2_res.append(colored(tok.string, "green"))
        prev_col = tok.end[1]
    l1_str = colored("0 ", "red") + "".join(l1_res)
    l2_str = colored("1 ", "green") + "".join(l2_res)
    return l1_str, l2_str


# given two tokenized python files, return the colored diff between them
def diff_src(src1, src2):
    comp = mss.mss_comp_aux(token_comp)
    mss_res = mss.MostSimilarSubsequence(src1, src2, comp)
    _, _, s1_ids, s2_ids = (
        mss_res.mss(),
        mss_res.similarity("mean"),
        mss_res.s_sub,
        mss_res.t_sub,
    )
    i, j = 0, 0
    res = []
    # iterate over the matching lines
    for match_i, match_j in zip(s1_ids, s2_ids):
        while i < match_i:
            line_i = str_line(src1[i], color=False)
            res.append(colored(f"< {line_i}", "red"))
            i += 1
        while j < match_j:
            line_j = str_line(src2[j], color=False)
            res.append(colored(f"> {line_j}", "green"))
            j += 1
        # compare if the lines are the same
        ij_sim = mss.MostSimilarSubsequence(src1[i], src2[j], comp).similarity("mean")
        if ij_sim == 1:
            line_i = str_line(src1[i], color=False)
            res.append(colored(f"  {line_i}", "white"))
        else:
            l1_str, l2_str = diff_line_new(src1[i], src2[j])
            res.append(l1_str)
            res.append(l2_str)
            res.append("")
        i = match_i + 1
        j = match_j + 1
    # add the remaining lines
    while i < len(src1):
        line_i = str_line(src1[i], color=True)
        res.append(colored(f"< {line_i}", "red"))
        i += 1
    while j < len(src2):
        line_j = str_line(src2[j], color=True)
        res.append(colored(f"> {line_j}", "green"))
        j += 1
    return "\n".join(res)


# return formatted string of a tokenized python file with holes
def str_sketch(sketch):
    res = []
    prev_line = None
    for line in sketch:
        if not line:
            continue
        if line == mss.HOLE:
            if prev_line == mss.HOLE:
                continue
            res.append(colored(" ...", "white"))
        else:
            res.append(str_line_ugly(line, color=True))
        prev_line = line
    return "\n".join(res)


def print_split_view(sgg1, sgg2):
    print(colored("<<<", "light_red"))
    for line in sgg1:
        print(colored("< ", "light_red") + str_tokens(line, color=True))
    print()
    print(colored(">>>", "light_green"))
    for line in sgg2:
        print(colored("> ", "light_green") + str_tokens(line, color=True))
    print()


def print_match_view(sgg1, sgg2):
    print(colored("~~~", "light_blue"))
    mss_res = mss.MostSimilarSubsequence(sgg1, sgg2, mss.line_comp)
    print(
        colored(
            f"sim: {mss_res.similarity('mean'):.4f} mss: {mss_res.mss():.4f}",
            "light_blue",
        )
    )
    i, j = 0, 0
    partial_matches = 0
    for m_i, m_j in zip(mss_res.s_sub, mss_res.t_sub):
        while i < m_i:
            print(colored("< " + str_tokens(sgg1[i]), "red"))
            # print(colored(f"{'<': <2}", "white", "on_red") + colored(str_tokens(sgg1[i]), "red"))
            i += 1
        while j < m_j:
            print(colored("> " + str_tokens(sgg2[j]), "green"))
            # print(colored(f"{'<': <2}", "black", "on_green") + colored(str_tokens(sgg2[j]), "green"))
            j += 1
        if sgg1[i] == sgg2[j]:
            print(colored("  " + str_tokens(sgg1[i]), "dark_grey"))
        else:
            partial_matches += 1
            l1, l2 = sgg1[i], sgg2[j]
            diff_line(l1, l2, partial_matches)
        i = m_i + 1
        j = m_j + 1


def diff(sgg1, sgg2):
    print_split_view(sgg1, sgg2)
    print_match_view(sgg1, sgg2)


def simm(sgg1, sgg2):
    mss_res = mss.MostSimilarSubsequence(sgg1, sgg2, mss.line_comp)
    print(
        colored(
            f"sim: {mss_res.similarity('mean'):.4f} mss: {mss_res.mss():.4f}",
            "light_blue",
        )
    )
    prev_i, prev_j = 0, 0
    partial_match_color = "white"
    # partial_match_color = "light_blue"
    for i, j in zip(mss_res.s_sub, mss_res.t_sub):
        if i - prev_i > 1 or j - prev_j > 1:
            print(colored("  ...", partial_match_color))
        l1, l2 = sgg1[i], sgg2[j]
        if l1 == l2:
            print("  " + str_tokens(l1, color=True))
        else:
            mss_line_res = mss.MostSimilarSubsequence(l1, l2, mss.token_comp)
            toks = []
            prev_h, prev_k = 0, 0
            for h, k in zip(mss_line_res.s_sub, mss_line_res.t_sub):
                if h - prev_h > 1 or k - prev_k > 1:
                    toks.append(colored("...", partial_match_color))
                t1, t2 = l1[h], l2[k]
                if t1 == t2:
                    toks.append(str_tokens([t1], color=True))
                else:
                    toks.append(
                        colored(
                            f"{str_tokens([t1])}",
                            partial_match_color,
                            attrs=["concealed"],
                        )
                    )
                prev_h, prev_k = h, k
            if prev_h < len(l1) - 1 or prev_k < len(l2) - 1:
                toks.append(colored("...", partial_match_color))
            print("  " + " ".join(toks))
        prev_i, prev_j = i, j


def explore(hc_obj=None):
    if hc_obj is None:
        # file_to_read = "./tasks/logs/2023-08-17_16-55-09.json"  # Networks Suggestions
        file_to_read = "./tasks/logs/2023-08-16_13-25-18.json"  # Rain Water Suggestions
        # file_to_read = "./tasks/logs/2023-08-22_16-00-34.json"  # Find markdown
        # file_to_read = "./tasks/logs/2023-08-17_12-06-52.json"  # Inverted triples
        with open(file_to_read, "r") as f:
            json_obj = json.load(f)
        print(f"Loaded {file_to_read}")

        prompt = json_obj["prompt"]
        suggestions = data.load_suggestions(prompt)

        hc_obj = mss.HierarchicalClustering(
            suggestions,
            lambda x, y: mss.MostSimilarSubsequence(
                x, y, comp=mss.line_comp
            ).similarity("mean"),
            method="complete",
        )

    start = 2 * hc_obj.get_size() - 2
    n = hc_obj.get_size()
    cur = start
    while cur >= n:
        left = int(hc_obj.hac_res[cur - n, 0])
        right = int(hc_obj.hac_res[cur - n, 1])
        l_cl = hc_obj.get_cluster(left)
        r_cl = hc_obj.get_cluster(right)
        # l_ctr = hc_obj.centroid(l_cl)
        # r_ctr = hc_obj.centroid(r_cl)
        l_ctr = hc_obj.chebyshev_center(l_cl)
        r_ctr = hc_obj.chebyshev_center(r_cl)
        sg1 = hc_obj.objs[l_ctr]
        sg2 = hc_obj.objs[r_ctr]
        diff(sg1, sg2)
        print(f"l: {len(l_cl)} r: {len(r_cl)}")
        print(f"left sample is: {l_ctr}\nright sample is: {r_ctr}")
        side = input("Left or right? (l/r): ")
        if side == "l":
            cur = left
        else:
            cur = right


if __name__ == "__main__":
    explore()
