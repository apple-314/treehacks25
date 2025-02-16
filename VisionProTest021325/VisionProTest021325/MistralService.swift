
//
//import SwiftUI
//import RealityKit
//import RealityKitContent
//
//// MARK: - Mistral Service
//class MistralService: ObservableObject {
//    @Published var isLoading = false
//    @Published var modelLoaded = false
//    
//    private let modelPath = "mistral-7b-v0.1.Q4_K_M.gguf"
//    private var context: Int32 = 0
//    
//    init() {
//        loadModel()
//    }
//    
//    private func loadModel() {
//        isLoading = true
//        
//        // Initialize Mistral model
//        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
//            // Simulated model loading
//            Thread.sleep(forTimeInterval: 2)
//            
//            DispatchQueue.main.async {
//                self?.isLoading = false
//                self?.modelLoaded = true
//            }
//        }
//    }
//    
//    func generateResponse(prompt: String) async throws -> String {
//        try await Task.sleep(nanoseconds: 2 * 1_000_000_000)
//        return "This is a simulated response from Mistral. Replace this with actual model inference."
//    }
//}
//
//// MARK: - Data Models
//struct ChatMessage: Identifiable {
//    let id = UUID()
//    let content: String
//    let isUser: Bool
//}
//
//// MARK: - Views
//struct MessageBubble: View {
//    let message: ChatMessage
//    
//    var body: some View {
//        HStack {
//            if message.isUser {
//                Spacer()
//            }
//            
//            Text(message.content)
//                .padding()
//                .background(message.isUser ? Color.blue : Color.gray)
//                .foregroundColor(.white)
//                .cornerRadius(15)
//                .frame(maxWidth: 600, alignment: message.isUser ? .trailing : .leading)
//            
//            if !message.isUser {
//                Spacer()
//            }
//        }
//    }
//}
//
//struct ChatView: View {
//    @StateObject private var mistralService = MistralService()
//    @State private var promptText = ""
//    @State private var chatMessages: [ChatMessage] = []
//    @State private var isGenerating = false
//    
//    var body: some View {
//        VStack {
//            if mistralService.isLoading {
//                loadingView
//            } else {
//                chatInterface
//            }
//        }
//        .padding()
//    }
//    
//    private var loadingView: some View {
//        VStack {
//            ProgressView()
//                .scaleEffect(1.5)
//            Text("Loading Mistral Model...")
//                .font(.headline)
//                .padding()
//        }
//    }
//    
//    private var chatInterface: some View {
//        VStack {
//            ScrollView {
//                LazyVStack(alignment: .leading, spacing: 12) {
//                    ForEach(chatMessages) { message in
//                        MessageBubble(message: message)
//                    }
//                }
//                .padding()
//            }
//            .frame(maxWidth: .infinity, maxHeight: .infinity)
//            .background(Color(.systemGray6))
//            
//            HStack {
//                TextField("Enter your prompt...", text: $promptText)
//                    .textFieldStyle(RoundedBorderTextFieldStyle())
//                    .disabled(isGenerating)
//                
//                Button(action: sendPrompt) {
//                    Image(systemName: "arrow.up.circle.fill")
//                        .resizable()
//                        .frame(width: 30, height: 30)
//                        .foregroundColor(.blue)
//                }
//                .disabled(promptText.isEmpty || isGenerating)
//            }
//            .padding()
//        }
//        .frame(width: 800, height: 600)
//    }
//    
//    private func sendPrompt() {
//        let userMessage = ChatMessage(content: promptText, isUser: true)
//        chatMessages.append(userMessage)
//        let promptToSend = promptText
//        promptText = ""
//        isGenerating = true
//        
//        Task {
//            do {
//                let response = try await mistralService.generateResponse(prompt: promptToSend)
//                await MainActor.run {
//                    chatMessages.append(ChatMessage(content: response, isUser: false))
//                    isGenerating = false
//                }
//            } catch {
//                await MainActor.run {
//                    chatMessages.append(ChatMessage(content: "Error: \(error.localizedDescription)", isUser: false))
//                    isGenerating = false
//                }
//            }
//        }
//    }
//}
//
//
////
////struct ContentView: View {
////    var body: some View {
////        ChatView()
////            .padding()
////    }
////}
////
////#Preview(windowStyle: .automatic) {
////    ContentView()
////}
