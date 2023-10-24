lemma LemmaFlattenLengthLeMul<T>(s: seq<seq<T>>, j: int)
  requires forall i {{:trigger s[i]}} | 0 <= i < |s| :: |s[i]| <= j
  ensures |FlattenReverse(s)| <= |s| * j
  {{
    if |s| == 0 {{
    }} else {{
      LemmaFlattenLengthLeMul(s[..|s|-1], j);
    }}
  }}
  # https://github.com/dafny-lang/libraries/pull/56/commits/4586789e1af32732224d7b7c31ccb55035ffac04
