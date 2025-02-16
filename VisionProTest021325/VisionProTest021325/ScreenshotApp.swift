//import SwiftUI
//import RealityKit
//import ARKit
//import RealityKitContent
//
//@main
//struct ScreenshotApp: App {
//    var body: some Scene {
//        WindowGroup {
//            ContentView()
//        }
//
//        ImmersiveSpace(id: "ImmersiveSpace") {
//            EmptyView()
//        }
//}
//
//// Rest of the code remains the same...
//class ScreenshotManager: ObservableObject {
//    @Published var lastScreenshot: UIImage?
//    @Published var showSuccessAlert = false
//    
//    func captureScreenshot(in rect: CGRect) {
//        // Take a snapshot of the current window
//        guard let window = UIApplication.shared.windows.first else { return }
//        
//        let renderer = UIGraphicsImageRenderer(bounds: rect)
//        let screenshot = renderer.image { context in
//            window.drawHierarchy(in: window.bounds, afterScreenUpdates: true)
//        }
//        
//        DispatchQueue.main.async {
//            self.lastScreenshot = screenshot
//            self.showSuccessAlert = true
//            self.sendToBackend(screenshot)
//        }
//    }
//    
//    private func sendToBackend(_ image: UIImage) {
//        guard let imageData = image.pngData() else { return }
//        
//        // Create URL request
//        guard let url = URL(string: "YOUR_BACKEND_URL_HERE") else { return }
//        var request = URLRequest(url: url)
//        request.httpMethod = "POST"
//        request.setValue("image/png", forHTTPHeaderField: "Content-Type")
//        
//        // Create upload task
//        let task = URLSession.shared.uploadTask(with: request, from: imageData) { data, response, error in
//            if let error = error {
//                print("Upload failed: \(error)")
//                return
//            }
//            
//            if let httpResponse = response as? HTTPURLResponse {
//                print("Upload completed with status: \(httpResponse.statusCode)")
//            }
//        }
//        
//        task.resume()
//    }
//}
//
//struct SelectionView: View {
//    @Binding var selectionRect: CGRect
//    @Binding var startPoint: CGPoint?
//    var onSelectionComplete: (CGRect) -> Void
//    
//    var body: some View {
//        GeometryReader { geometry in
//            ZStack {
//                Color.black.opacity(0.3)
//                    .overlay(
//                        Rectangle()
//                            .path(in: selectionRect)
//                            .fill(Color.blue.opacity(0.2))
//                    )
//                    .mask(
//                        Rectangle()
//                            .path(in: selectionRect)
//                            .fill(style: FillStyle(eoFill: true))
//                    )
//            }
//            .gesture(
//                DragGesture(minimumDistance: 0)
//                    .onChanged { value in
//                        if startPoint == nil {
//                            startPoint = value.location
//                        }
//                        
//                        let width = value.location.x - (startPoint?.x ?? 0)
//                        let height = value.location.y - (startPoint?.y ?? 0)
//                        
//                        selectionRect = CGRect(
//                            x: width > 0 ? startPoint?.x ?? 0 : value.location.x,
//                            y: height > 0 ? startPoint?.y ?? 0 : value.location.y,
//                            width: abs(width),
//                            height: abs(height)
//                        )
//                    }
//                    .onEnded { value in
//                        if selectionRect.width > 10 && selectionRect.height > 10 {
//                            onSelectionComplete(selectionRect)
//                        }
//                        startPoint = nil
//                        selectionRect = .zero
//                    }
//            )
//        }
//    }
//}
