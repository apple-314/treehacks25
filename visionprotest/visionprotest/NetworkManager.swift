import SwiftUI

class NetworkManager {
    static func captureGesture() {
        // URL of your FastAPI endpoint for capturing gestures
        guard let url = URL(string: "http://127.0.0.1:8000/capture_gesture") else {
            print("Invalid URL")
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // Generate a timestamp in ISO8601 format.
        let timestamp = ISO8601DateFormatter().string(from: Date())
        let body: [String: String] = ["timestamp": timestamp]
        
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: body, options: [])
            request.httpBody = jsonData
        } catch {
            print("Error creating JSON data: \(error)")
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Error capturing gesture: \(error)")
                return
            }
            
            if let data = data,
               let jsonResponse = try? JSONSerialization.jsonObject(with: data, options: []) {
                print("API Response: \(jsonResponse)")
            }
        }.resume()
    }
}
