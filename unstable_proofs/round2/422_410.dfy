  function method Encode(b: seq<uint8>): (s: seq<char>)
    ensures StringIs7Bit(s)
    ensures |s| % 4 == 0
    ensures IsBase64String(s)
    // Rather than ensure Decode(s) == Success(b) directly, lemmas are used to verify this property
  {
    if |b| % 3 == 0 then
      EncodeUnpadded(b)
    else if |b| % 3 == 1 then
      assert |b| >= 1;
      EncodeUnpadded(b[..(|b| - 1)]) + Encode2Padding(b[(|b| - 1)..])
    else
      assert |b| % 3 == 2;
      assert |b| >= 2;
      EncodeUnpadded(b[..(|b| - 2)]) + Encode1Padding(b[(|b| - 2)..])
  }
https://github.com/aws/aws-encryption-sdk-dafny/pull/422/files
