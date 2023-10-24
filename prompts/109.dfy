type byte = BoundedInts.uint8
/**
  * Returns the byte serialization of the given code unit sequence.
  */
function Serialize(s: Utf8EncodingForm.CodeUnitSeq): (b: seq<byte>)
{
  Seq.Map(c => c as byte, s)
}
/**
  * Returns the code unit sequence that serializes to the given byte sequence.
  */
function Deserialize(b: seq<byte>): (s: Utf8EncodingForm.CodeUnitSeq)
{
  Seq.Map(b => b as Utf8EncodingForm.CodeUnit, b)
}
/**
  * Serializing a code unit sequence and then deserializing the result, yields the original code unit sequence.
  */
lemma LemmaSerializeDeserialize(s: Utf8EncodingForm.CodeUnitSeq)
  ensures Deserialize(Serialize(s)) == s
{
}
/**
  * Deserializing a byte sequence and then serializing the result, yields the original byte sequence.
  */
lemma LemmaDeserializeSerialize(b: seq<byte>)
  ensures Serialize(Deserialize(b)) == b
{
}
# https://github.com/dafny-lang/libraries/pull/109/files
