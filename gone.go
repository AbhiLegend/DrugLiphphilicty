package main

import (
    "bufio"
    "bytes"
    "encoding/json"
    "fmt"
    "io/ioutil"
    "net/http"
    "os"
    "strings"
)

type PredictionRequest struct {
    Smiles string `json:"smiles"`
}

type PredictionResponse struct {
    Prediction float64 `json:"prediction"`
    ImagePath  string  `json:"image_path"`
    Error      string  `json:"error"`
}

func makePredictionRequest(apiURL, smiles string) {
    requestPayload := PredictionRequest{Smiles: smiles}
    jsonData, err := json.Marshal(requestPayload)
    if err != nil {
        fmt.Println("Error marshalling input data:", err)
        return
    }

    resp, err := http.Post(apiURL, "application/json", bytes.NewBuffer(jsonData))
    if err != nil {
        fmt.Println("Error making request:", err)
        return
    }
    defer resp.Body.Close()

    var response PredictionResponse
    body, err := ioutil.ReadAll(resp.Body)
    if err != nil {
        fmt.Println("Error reading response body:", err)
        return
    }

    err = json.Unmarshal(body, &response)
    if err != nil {
        fmt.Println("Error unmarshalling response:", err)
        return
    }

    if response.Error != "" {
        fmt.Println("Error:", response.Error)
        return
    }

    fmt.Printf("Predicted Lipophilicity for '%s': %f\n", smiles, response.Prediction)

    if response.ImagePath != "" {
        fmt.Println("Molecule image saved at:", response.ImagePath)
    }
}

func main() {
    flaskAPIURL := "http://localhost:5000/predict"
    scanner := bufio.NewScanner(os.Stdin)

    fmt.Println("Enter SMILES strings separated by commas for lipophilicity prediction:")
    scanner.Scan()
    input := scanner.Text()

    smilesStrings := strings.Split(input, ",")
    for _, smiles := range smilesStrings {
        smiles = strings.TrimSpace(smiles)
        fmt.Printf("Sending prediction request for: %s\n", smiles)
        makePredictionRequest(flaskAPIURL, smiles)
    }
}
