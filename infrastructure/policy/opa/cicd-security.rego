package cicd.security

import rego.v1

deny contains msg if {
  some vulnerability in input.vulnerabilities
  vulnerability.severity == "CRITICAL"
  msg := sprintf(
    "Critical vulnerability detected in %s (%s) - blocking deploy",
    [vulnerability.component, vulnerability.id],
  )
}

allow if count(deny) == 0
