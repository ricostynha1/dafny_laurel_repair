ghost predicate IsLeftUnital<T(!new)>(bop: (T, T) -> T, unit: T) {
      forall x :: bop(unit, x) == x

}

ghost predicate IsRightUnital<T(!new)>(bop: (T, T) -> T, unit: T) {
      forall x :: bop(x, unit) == x

}

ghost predicate IsUnital<T(!new)>(bop: (T, T) -> T, unit: T) {
      && IsLeftUnital(bop, unit)
        && IsRightUnital(bop, unit)

}

lemma UnitIsUnique<T(!new)>(bop: (T, T) -> T, unit1: T, unit2: T)
  requires IsUnital(bop, unit1)
    requires IsUnital(bop, unit2)
      ensures unit1 == unit2
{
}
