import SwiftUI
import RealityKit

struct ContentView: View {
    @StateObject private var handTrackingModel = HandTrackingModel()
    @State private var scale: CGFloat = 1.0
    @State private var lastPinchTime = Date.distantPast
    @State private var responseMessage: String?
    @State private var debugText: String = "Waiting for gesture..."
    
    var body: some View {
        VStack {
            // Debug info
            Text(debugText)
                .font(.system(size: 14))
                .foregroundColor(.gray)
                .padding()
            
            Text("Pinch to capture gesture")
                .padding()
                .scaleEffect(scale)
                // Using multiple gestures to catch different types of interactions
                .gesture(
                    SpatialTapGesture(count: 1)
                        .onEnded { _ in
                            debugText = "Tap detected"
                            handleGesture()
                        }
                )
                .gesture(
                    MagnifyGesture()
                        .onChanged { value in
                            debugText = "Magnify: \(value.magnification)"
                            scale = value.magnification
                            
                            // More sensitive pinch detection
                            if value.magnification < 0.9 {  // Changed from 0.7 to 0.9
                                handleGesture()
                            }
                        }
                        .onEnded { _ in
                            debugText = "Gesture ended"
                            scale = 1.0
                        }
                )
                .simultaneousGesture(
                    DragGesture(minimumDistance: 0)
                        .onChanged { value in
                            debugText = "Drag: \(value.translation)"
                        }
                )
            
            if let message = handTrackingModel.lastResponse {
                Text(message)
                    .padding()
                    .font(.caption)
            }
            
            // Additional debug buttons
            HStack {
                Button("Test Gesture") {
                    debugText = "Manual test triggered"
                    handleGesture()
                }
                .padding()
                .background(Color.blue)
                .foregroundColor(.white)
                .cornerRadius(10)
                
                Button("Reset") {
                    debugText = "Reset triggered"
                    scale = 1.0
                    lastPinchTime = Date.distantPast
                }
                .padding()
                .background(Color.red)
                .foregroundColor(.white)
                .cornerRadius(10)
            }
        }
    }
    
    private func handleGesture() {
        let currentTime = Date()
        if currentTime.timeIntervalSince(lastPinchTime) > 1.0 {
            debugText = "Gesture detected and processed!"
            lastPinchTime = currentTime
            handTrackingModel.handlePinchGesture()
        } else {
            debugText = "Gesture ignored (cooldown)"
        }
    }
}

// HandTrackingModel remains the same as before
class HandTrackingModel: ObservableObject {
    @Published var lastResponse: String?
    private var lastInteractionTime: Date = Date.distantPast
    private let cooldown: TimeInterval = 1.0
    
    func handlePinchGesture() {
        let currentTime = Date()
        guard currentTime.timeIntervalSince(lastInteractionTime) >= cooldown else {
            print("DEBUG: Interaction ignored - cooldown period")
            return
        }
        
        print("DEBUG: Processing pinch gesture")
        lastInteractionTime = currentTime
        
        let dateFormatter = ISO8601DateFormatter()
        dateFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        let timestampString = dateFormatter.string(from: currentTime)
        
        sendGestureToEndpoint(timestamp: timestampString)
    }
    
    private func sendGestureToEndpoint(timestamp: String) {
        print("DEBUG: Sending timestamp to /capture_gesture")
        guard let url = URL(string: "http://172.20.10.15:8000/capture_gesture") else {
            print("DEBUG: Invalid URL")
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = ["timestamp": timestamp]
        
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: body)
            request.httpBody = jsonData
            print("DEBUG: Sending request with timestamp: \(timestamp)")
            
            let task = URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
                if let error = error {
                    print("DEBUG: Error sending gesture: \(error)")
                    return
                }
                
                if let data = data,
                   let response = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let message = response["message"] as? String {
                    DispatchQueue.main.async {
                        self?.lastResponse = message
                        print("DEBUG: Server response: \(message)")
                    }
                }
            }
            task.resume()
        } catch {
            print("DEBUG: Error creating request: \(error)")
        }
    }
}

#Preview {
    ContentView()
}
