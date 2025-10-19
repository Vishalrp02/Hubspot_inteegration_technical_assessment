import { useState } from "react";
import { Box, Autocomplete, TextField } from "@mui/material";
import { AirtableIntegration } from "./integrations/airtable";
import { NotionIntegration } from "./integrations/notion";
import { HubspotIntegration } from "./integrations/hubspot";
import { DataForm } from "./data-form";

const integrationMapping = {
  Notion: NotionIntegration,
  Airtable: AirtableIntegration,
  Hubspot: HubspotIntegration,
};

export const IntegrationForm = () => {
  const [integrationParams, setIntegrationParams] = useState({});
  const [user, setUser] = useState("TestUser");
  const [org, setOrg] = useState("TestOrg");
  const [currType, setCurrType] = useState(null);
  const CurrIntegration = integrationMapping[currType];

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      gap={3} // consistent vertical spacing
      sx={{ width: "100%", maxWidth: 600, mx: "auto", mt: 4 }}
    >
      {/* User / Org / Integration Type Inputs */}
      <Box display="flex" flexDirection="column" gap={2} width="100%">
        <TextField
          label="User"
          value={user}
          onChange={(e) => setUser(e.target.value)}
        />
        <TextField
          label="Organization"
          value={org}
          onChange={(e) => setOrg(e.target.value)}
        />
        <Autocomplete
          id="integration-type"
          options={Object.keys(integrationMapping)}
          renderInput={(params) => (
            <TextField {...params} label="Integration Type" />
          )}
          onChange={(e, value) => setCurrType(value)}
        />
      </Box>

      {/* Integration-specific component */}
      {currType && (
        <Box width="100%">
          <CurrIntegration
            user={user}
            org={org}
            integrationParams={integrationParams}
            setIntegrationParams={setIntegrationParams}
          />
        </Box>
      )}

      {/* DataForm for loaded credentials */}
      {integrationParams?.credentials && (
        <Box width="100%">
          <DataForm
            integrationType={integrationParams?.type}
            credentials={integrationParams?.credentials}
          />
        </Box>
      )}
    </Box>
  );
};
