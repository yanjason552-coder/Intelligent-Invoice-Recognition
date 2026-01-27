import { Container } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"

import SchemaMonitoring from "@/components/Dashboard/SchemaMonitoring"

export const Route = createFileRoute("/_layout/schema-monitoring")({
  component: SchemaMonitoringPage,
})

function SchemaMonitoringPage() {
  return (
    <Container maxW="full" p={0}>
      <SchemaMonitoring />
    </Container>
  )
}
