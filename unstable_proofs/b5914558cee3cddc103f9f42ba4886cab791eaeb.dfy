  lemma {:vcs_split_on_every_assert} ProbUnifCorrectnessEvenCaseIff(n: nat, s: RNG, m: nat)
    requires m % 2 == 0
    requires n > 0
    ensures
      var a := ProbUnif(n / 2)(s).0;
      var b := Deconstruct(ProbUnif(n / 2)(s).1).0;
      ProbUnif(n)(s).0 == m <==> (!b && 2*a == m)
  {
    var a := ProbUnif(n / 2)(s).0;
    var b := Deconstruct(ProbUnif(n / 2)(s).1).0;
    if ProbUnif(n)(s).0 == m {
      if (b && 2*a + 1 == m) {
        assert A: (2*a + 1) / 2 == 1 by {
          calc {
            (2*a + 1) / 2;
          == { LemmaAboutNatDivision(2*a + 1, 2); }
            ((2*a + 1) as real / 2 as real).Floor;
            (1 as real).Floor;
          ==
            1;
          }
        }
        assert m % 2 == 1 by { assert m == 2*a + 1; reveal A; assert m / 2 == 1 by { DivisionSubstituteAlternative(2, m, 2*a + 1); } }
        assert m % 2 == 0;
        assert false;
      }
      assert !(b && 2*a + 1 == m) ==> (!b && 2*a == m) by {
        ProbUnifCorrectnessIff(n, s, m);
        assert (b && 2*a + 1 == m) || (!b && 2*a == m);
      }
    }
    if (!b && 2*a == m) {
      assert (b && 2*a + 1 == m) || (!b && 2*a == m);
      assert ProbUnif(n)(s).0 == m by { ProbUnifCorrectnessIff(n, s, m); }
    }
  }
  https://github.com/dafny-lang/Dafny-VMC/pull/33/commits/b5914558cee3cddc103f9f42ba4886cab791eaeb
