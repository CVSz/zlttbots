package singularity

deny[msg] {
  input.finding.severity == "error"
  msg := "Critical vulnerability blocks release"
}
