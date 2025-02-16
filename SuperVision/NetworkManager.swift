import SwiftUI

class NetworkManager {
    static func captureGesture(completion: @escaping (Result<Profile, Error>) -> Void) {
        guard let url = URL(string: "https://normal-guiding-orca.ngrok-free.app/capture_gesture") else {
            completion(.failure(URLError(.badURL)))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let timestamp = ISO8601DateFormatter().string(from: Date())
        let body: [String: String] = ["timestamp": timestamp]
        
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: body, options: [])
            request.httpBody = jsonData
        } catch {
            print("Error creating JSON data: \(error)")
            completion(.failure(error))
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Error capturing gesture: \(error)")
                completion(.failure(error))
                return
            }
            guard let data = data else {
                let error = URLError(.badServerResponse)
                completion(.failure(error))
                return
            }
            do {
                let decoder = JSONDecoder()
                let captureResponse = try decoder.decode(CaptureResponse.self, from: data)
                print("API Response Message: \(captureResponse.message)")
                completion(.success(captureResponse.profile))
            } catch {
                print("Error decoding JSON: \(error)")
                if let jsonString = String(data: data, encoding: .utf8) {
                    print("Raw JSON: \(jsonString)")
                }
                completion(.failure(error))
            }
        }.resume()
    }
}
