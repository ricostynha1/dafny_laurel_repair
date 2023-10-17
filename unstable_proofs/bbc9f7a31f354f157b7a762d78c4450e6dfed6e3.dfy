  lemma SortedByLessThanOrEqualTo(s: seq<int>) 
    requires SortedBy(s, (x, y) => x <= y)
    ensures SortedBy(s, (x, y) => x < y || x == y)
  {}

  method {:vcs_split_on_every_assert} SortAndSearch() {
    var input := [1, 7, 7, 3, 9, 0, -6];
    
    var sortedInput := MergeSortBy(input, (x, y) => x <= y);
    print sortedInput, "\n";

    var sortedArray := ToArray(sortedInput);
    SortedByLessThanOrEqualTo(sortedArray[..]);
    var indexOfThree := BinarySearch.BinarySearch(sortedArray, 3, (x, y) => x < y);
    if indexOfThree.Some? {
      print indexOfThree.value, "\n";
    } else {
      print "Not found\n";
    }
  }

  method Main() {
    SortAndSearch();
  }
  https://github.com/dafny-lang/libraries/pull/76/commits/bbc9f7a31f354f157b7a762d78c4450e6dfed6e3
