  lemma DualOfUTF8(utf: UTF8.ValidUTF8Bytes, remainder: seq<uint8>)
    requires |utf| < UINT16_LIMIT && UTF8.ValidUTF8Seq(utf)
    ensures var serializedUtf := UInt16ToSeq(|utf| as uint16) + utf + remainder;
      GetUTF8(serializedUtf[2..], |utf|) == Some(utf)
  {
    var serializedUtf := UInt16ToSeq(|utf| as uint16) + utf + remainder;
    var serial := serializedUtf[2..];
    var deserializedUTF := GetUTF8(serial, |utf|);
    // seq to UTF8 casting is not done automatically by Dafny and needs to be done manually
    assert deserializedUTF.Some? by {
      assert serial[..|utf|] == utf;
      assert |serial| >= |utf| && UTF8.ValidUTF8Seq(serial[..|utf|]);
    }
  }
  https://github.com/aws/aws-encryption-sdk-dafny/pull/364/commits/952f2aee8ff0c062267b9f42c913cf911701f6e6
