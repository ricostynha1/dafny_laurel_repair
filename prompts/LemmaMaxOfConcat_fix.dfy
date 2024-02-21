  lemma LemmaMaxOfConcat(xs: seq<int>, ys: seq<int>)
    requires 0 < |xs| && 0 < |ys|
    ensures Max(xs+ys) >= Max(xs)
    ensures Max(xs+ys) >= Max(ys)
    ensures forall i {:trigger i in [Max(xs + ys)]} :: i in xs + ys ==> Max(xs + ys) >= i
  {
    reveal Max();
    if |xs| == 1 {
      assert  xs+ys == [xs[0]] + (xs[1..] + ys);
    } else {
      assert  xs+ys == [xs[0]] + (xs[1..] + ys);
      LemmaMaxOfConcat(xs[1..], ys);
    }
  }
