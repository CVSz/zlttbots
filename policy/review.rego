package review

deny[msg] {
  some i
  lower(input[i].severity) == "critical"
  msg := sprintf("Critical issue in %s:%d", [input[i].file, input[i].line])
}

deny[msg] {
  some i
  lower(input[i].severity) == "high"
  contains(lower(input[i].comment), "sql injection")
  msg := sprintf("Potential SQL injection in %s:%d", [input[i].file, input[i].line])
}
