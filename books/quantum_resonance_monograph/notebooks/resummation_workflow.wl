(* Quantum Resonance as a Global Connection Problem
   Compact resummation workflow for Appendix A.
   Wolfram Language source; no notebook front end is required. *)

ClearAll[quarticExact, quarticCoefficient, quarticTruncated,
  borelPolynomial, borelPade, borelPadeSum, borelPoles,
  odmMap, odmSeries, odmRoots, odmValue];

quarticExact[g_?NumericQ, precision_: 50] :=
  N[Exp[1/(8 g)] BesselK[1/4, 1/(8 g)]/(2 Sqrt[Pi g]),
    precision];

quarticCoefficient[n_Integer?NonNegative] :=
  (-1)^n Gamma[2 n + 1/2]/(Sqrt[Pi] n!);

quarticTruncated[g_, order_Integer?NonNegative] :=
  Sum[quarticCoefficient[n] g^n, {n, 0, order}];

borelPolynomial[t_, order_Integer?NonNegative] :=
  Sum[quarticCoefficient[n] t^n/n!, {n, 0, order}];

borelPade[t_, order_Integer?Positive] := Module[{left, right},
  left = Floor[order/2];
  right = order - left;
  PadeApproximant[borelPolynomial[t, order], {t, 0, {left, right}}]
];

borelPoles[order_Integer?Positive, precision_: 50] := Module[{t},
  t /. N[Solve[Denominator[Together[borelPade[t, order]]] == 0, t],
    precision]
];

borelPadeSum[g_?NumericQ, order_Integer?Positive,
    precision_: 50] := Module[{t, rational},
  rational = borelPade[t, order];
  NIntegrate[Exp[-t/g] rational/g, {t, 0, Infinity},
    WorkingPrecision -> precision,
    AccuracyGoal -> Floor[precision/2],
    PrecisionGoal -> Floor[precision/2]]
];

odmMap[lambda_, rho_] := rho lambda/(1 - lambda)^2;

odmSeries[lambda_, rho_, order_Integer?Positive] :=
  Normal@Series[
    Sum[quarticCoefficient[n] odmMap[lambda, rho]^n,
      {n, 0, order}], {lambda, 0, order}];

odmRoots[order_Integer?Positive, precision_: 50] := Module[
  {lambda, rho, highest},
  highest = Coefficient[odmSeries[lambda, rho, order], lambda, order];
  Select[rho /. NSolve[highest == 0, rho, WorkingPrecision -> precision],
    Im[#] == 0 && Re[#] > 0 &]
];

odmValue[g_?NumericQ, order_Integer?Positive, rho_?NumericQ,
    precision_: 50] := Module[{lambda, physicalRoot},
  physicalRoot = lambda /. FindRoot[
    g == odmMap[lambda, rho], {lambda, Min[0.8, g/(g + rho)]},
    WorkingPrecision -> precision];
  N[odmSeries[lambda, rho, order] /. lambda -> physicalRoot, precision]
];

(* Reproducible benchmark.  Inspect borelPoles before integrating. *)
Do[
  Print["g = ", g, ", exact = ", quarticExact[g, 40]];
  Print["Borel-Pade, N = 20: ", borelPadeSum[g, 20, 40]],
  {g, {1/5, 2/5}}
];

