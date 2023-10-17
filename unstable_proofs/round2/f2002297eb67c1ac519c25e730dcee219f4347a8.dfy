  lemma AboutDecodeValid(s: seq<char>, b: seq<uint8>)
    requires IsBase64String(s) && b == DecodeValid(s)
    ensures 4 <= |s| ==> var finalBlockStart := |s| - 4;
      var prefix, suffix := s[..finalBlockStart], s[finalBlockStart..];
      && (Is1Padding(suffix) ==> |b| % 3 == 2)
      && (Is2Padding(suffix) ==> |b| % 3 == 1)
      && (!Is1Padding(suffix) && !Is2Padding(suffix) ==> |b| % 3 == 0)
  {
    var finalBlockStart := |s| - 4;
    if s == [] {
    } else if Is1Padding(s[finalBlockStart..]) {
      assert b == DecodeUnpadded(s[..finalBlockStart]) + Decode1Padding(s[finalBlockStart..]);
    } else if Is2Padding(s[finalBlockStart..]) {
      assert b == DecodeUnpadded(s[..finalBlockStart]) + Decode2Padding(s[finalBlockStart..]);
    } else {
      assert b == DecodeUnpadded(s);
    }
  }
  https://github.com/aws/aws-encryption-sdk-dafny/pull/364/commits/f2002297eb67c1ac519c25e730dcee219f4347a8#diff-b883a0a1e1450858a57afaf9f5df4c79a6d263714a3e470987c36c5a91d6fb48L363-L377
