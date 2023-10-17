  lemma InSingleFalseTypes(r: Request, s: EntityStore, e1: Expr, e2: Expr, t1: Type, t2: Type)
    requires subty(t1,Type.Entity(AnyEntity))
    requires subty(t2,Type.Entity(AnyEntity))
    requires IsSafe(r,s,e1,t1)
    requires IsSafe(r,s,e2,t2)
    requires forall u1, u2: EntityUID |
               InstanceOfType(Value.EntityUID(u1), t1) && InstanceOfType(Value.EntityUID(u2), t2) ::
               !EntityInEntity(s,u1,u2)
    ensures IsFalse(r,s,BinaryApp(BinaryOp.In,e1,e2))
  {
    var evaluator := Evaluator(r,s);
    var r1 := evaluator.interpret(e1);
    var r2 := evaluator.interpret(e2);
    var res := evaluator.interpret(BinaryApp(BinaryOp.In,e1,e2));

    reveal IsSafe();
    if r1.Err? {
      assert res == r1;
    } else if r2.Err? {
      assert res == r2;
    } else {
      assert res == evaluator.applyBinaryOp(BinaryOp.In,r1.value,r2.value);
      assert InstanceOfType(r1.value,t1);
      assert InstanceOfType(r2.value,t2);
      assert r1.value.Primitive? && r1.value.primitive.EntityUID?;
      assert r2.value.Primitive? && r2.value.primitive.EntityUID?;
      var u1 := r1.value.primitive.uid;
      var u2 := r2.value.primitive.uid;
      assert !EntityInEntity(s,u1,u2);
      assert res.value == Value.FALSE;
    }
  }
  https://github.com/cedar-policy/cedar-spec/blob/816b782e037c6440c3832289c08da315a936844c/cedar-dafny/validation/thm/model.dfy
