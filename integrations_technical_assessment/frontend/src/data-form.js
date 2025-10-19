import { useState } from "react";
import { Box, TextField, Button, Typography, Paper } from "@mui/material";
import axios from "axios";

const endpointMapping = {
  Notion: "notion",
  Airtable: "airtable",
  Hubspot: "hubspot",
};

export const DataForm = ({ integrationType, credentials }) => {
  const [loadedData, setLoadedData] = useState(null);
  const [loading, setLoading] = useState(false);
  const endpoint = endpointMapping[integrationType];

  const handleLoad = async () => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("credentials", JSON.stringify(credentials));

      const response = await axios.post(
        `http://localhost:8000/integrations/${endpoint}/load`,
        formData
      );

      setLoadedData(response.data);
    } catch (e) {
      alert(e?.response?.data?.detail || "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      width="100%"
      sx={{ p: 3 }}
    >
      <Typography variant="h6" gutterBottom>
        {integrationType} Integration
      </Typography>

      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        width="100%"
        maxWidth={600}
      >
        {/* Buttons aligned horizontally */}
        <Box display="flex" gap={2} width="100%" justifyContent="center" mb={2}>
          <Button onClick={handleLoad} variant="contained" disabled={loading}>
            {loading ? "Loading..." : "Load Data"}
          </Button>
          <Button onClick={() => setLoadedData(null)} variant="outlined">
            Clear Data
          </Button>
        </Box>

        {/* Loaded Data */}
        {loadedData && (
          <Box width="100%">
            {Array.isArray(loadedData) ? (
              loadedData.map((item, index) => (
                <Paper
                  key={index}
                  sx={{
                    p: 2,
                    mb: 2,
                    border: "1px solid #ccc",
                    borderRadius: 2,
                    backgroundColor: "#f9f9f9",
                  }}
                >
                  <Typography variant="subtitle1" fontWeight="bold">
                    {item.name || "Untitled"}
                  </Typography>
                  <Typography variant="body2">ID: {item.id}</Typography>
                  <Typography variant="body2">Type: {item.type}</Typography>
                  <Typography variant="body2">
                    Created: {item.creation_time || "N/A"}
                  </Typography>
                  <Typography variant="body2">
                    Updated: {item.last_modified_time || "N/A"}
                  </Typography>
                </Paper>
              ))
            ) : (
              <TextField
                label="Loaded Data (Raw)"
                value={JSON.stringify(loadedData, null, 2)}
                multiline
                minRows={6}
                fullWidth
                disabled
              />
            )}
          </Box>
        )}
      </Box>
    </Box>
  );
};
