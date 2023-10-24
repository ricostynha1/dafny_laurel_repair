  /* is true if there are no duplicate values in the sequence */
  predicate {:opaque} HasNoDuplicates<T>(s: seq<T>)
  {
    (forall i, j {:trigger s[i], s[j]}:: 0 <= i < |s| && 0 <= j < |s| && i != j ==> s[i] != s[j])
  }

  /* if sequence a and b don't have duplicates and there are no elements in
  common between them, then the concatenated sequence of a + b will not contain
  duplicates either */
  lemma LemmaNoDuplicatesInConcat<T>(a: seq<T>, b: seq<T>)
    requires HasNoDuplicates(a);
    requires HasNoDuplicates(b);
    requires multiset(a) !! multiset(b);
    ensures HasNoDuplicates(a+b);
  {
    reveal HasNoDuplicates();
    var c := a + b;
    if |c| > 1 {
        assert forall i, j {:trigger c[i], c[j]}:: i != j && 0 <= i < |a| && |a| <= j < |c| ==> c[i] in multiset(a) && c[j] in multiset(b) && c[i] != c[j];
    }
  }
# https://github.com/dafny-lang/libraries/pull/65/commits/5312bb551b7b6cad12a16d1fd678fc811da9e80a
