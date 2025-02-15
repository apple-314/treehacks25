import SwiftUI
import AVFoundation

struct AudioProcessing: View {
    @StateObject private var audioProcessor = AudioProcessor()
    
    // Example multiline description text.
    let descriptionText = """
    this is a cool project
    the project is very cool
    the project is insanely cool
    """
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // Name placeholder at the top (centered)
                VStack {
                    Text("Name Placeholder")
                        .font(.system(size: 50, weight: .bold, design: .rounded))
                        .padding(.top, geometry.safeAreaInsets.top + 20)
                    Spacer()
                }
                
                // Description placeholder on the left side as a bullet list.
                HStack {
                    VStack {
                        Spacer()
                        HStack {
                            BulletDescriptionView(descriptionText: descriptionText)
                            Spacer()
                        }
                        Spacer()
                    }
                    Spacer()
                }
                
                // Microphone button on the right side.
                HStack {
                    Spacer()
                    VStack {
                        Spacer()
                        Button(action: {
                            print("taking picture of person")
                        }) {
                            Image(systemName: "camera")
                                .resizable()
                                .scaledToFit()
                                .frame(width: 80, height: 80)
                                .foregroundColor(.white)
                                .padding()
                                .background(Color.black)
                                .clipShape(Circle())
                        }
                        .padding(.trailing, 20)
                        Spacer()
                        Button(action: {
                            if audioProcessor.isRecording {
                                audioProcessor.stopRecording()
                            } else {
                                audioProcessor.startRecording()
                            }
                        }) {
                            Image(systemName: audioProcessor.isRecording ? "mic.fill" : "mic")
                                .resizable()
                                .scaledToFit()
                                .frame(width: 80, height: 80)
                                .foregroundColor(.white)
                                .padding()
                                .background(audioProcessor.isRecording ? Color.red : Color.green)
                                .clipShape(Circle())
                        }
                        .padding(.trailing, 20)
                        Spacer()
                    }
                }
            }
        }
        .onAppear {
            audioProcessor.setupAudioSession()
        }
    }
}

struct BulletDescriptionView: View {
    let descriptionText: String
    
    // Splitting the text into bullet points based on "\n"
    var bulletPoints: [String] {
        descriptionText.components(separatedBy: "\n").filter { !$0.isEmpty }
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            ForEach(bulletPoints, id: \.self) { statement in
                HStack(alignment: .top, spacing: 4) {
                    Text("•")
                        .font(.system(size: 40, weight: .bold, design: .rounded))
                    Text(statement)
                        .font(.system(size: 40, weight: .bold, design: .rounded))
                }
            }
        }
        .frame(width: 400)
        .padding(8)
        .background(
            RoundedRectangle(cornerRadius: 15)
                .fill(Color.gray.opacity(0.4))
        )
        .padding(.leading, 20)
    }
}

class AudioProcessor: ObservableObject {
    private var audioEngine = AVAudioEngine()
    private var inputNode: AVAudioInputNode?
    private var audioFormat: AVAudioFormat?
    private var isAudioSessionConfigured = false
    private var audioFile: AVAudioFile? // For writing audio data
    private var fileURL: URL?          // Stores the file URL for logging
    
    @Published var isRecording = false
    @Published var audioLevel: Float = 0.0
    
    // Set these to the URL of your FastAPI endpoints.
    private let uploadURLString = "http://127.0.0.1:8000/upload_samples"
    private let finalizeString = "http://127.0.0.1:8000/finalize"
    
    func setupAudioSession() {
        let session = AVAudioSession.sharedInstance()
        do {
            try session.setCategory(.playAndRecord,
                                    mode: .default,
                                    options: [.defaultToSpeaker, .allowBluetooth])
            try session.setActive(true)
            isAudioSessionConfigured = true
        } catch {
            print("Failed to set up audio session: \(error)")
        }
    }
    
    func startRecording() {
        guard isAudioSessionConfigured else { return }
        
        let engine = audioEngine
        let inputNode = engine.inputNode
        let format = inputNode.outputFormat(forBus: 0)
        
        self.inputNode = inputNode
        self.audioFormat = format
        
        // Determine a writable directory based on the platform.
        #if os(visionOS)
        let directory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        #elseif os(macOS)
        let directory = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
        #else
        let directory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        #endif
        
        let fileName = "recording.wav"
        let fileURL = directory.appendingPathComponent(fileName)
        self.fileURL = fileURL  // Save for later logging
        
        do {
            // Remove an existing file if necessary.
            if FileManager.default.fileExists(atPath: fileURL.path) {
                try FileManager.default.removeItem(at: fileURL)
            }
            // Create an AVAudioFile for writing.
            audioFile = try AVAudioFile(forWriting: fileURL,
                                        settings: format.settings,
                                        commonFormat: .pcmFormatFloat32,
                                        interleaved: false)
            print("Audio file will be saved at: \(fileURL.path)")
        } catch {
            print("Error creating audio file: \(error)")
            return
        }
        
        // Install tap to process audio and write to file.
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: format) { buffer, _ in
            self.processAudio(buffer: buffer)
            do {
                try self.audioFile?.write(from: buffer)
            } catch {
                print("Error writing audio buffer to file: \(error)")
            }
        }
        
        do {
            try engine.start()
            isRecording = true
            print("🎤 Recording started...")
        } catch {
            print("Error starting audio engine: \(error)")
        }
    }
    
    func stopRecording() {
        audioEngine.stop()
        inputNode?.removeTap(onBus: 0)
        isRecording = false
        print("🛑 Recording stopped.")
        
        if let fileURL = fileURL {
            print("Audio file saved at: \(fileURL.path)")
        }
        finalizeSamples()
    }
    
    private func processAudio(buffer: AVAudioPCMBuffer) {
        guard let channelData = buffer.floatChannelData?[0] else { return }
        let channelDataArray = Array(UnsafeBufferPointer(start: channelData,
                                                         count: Int(buffer.frameLength)))
        // Compute average audio level (if needed).
        let level = channelDataArray.map { abs($0) }.reduce(0, +) / Float(channelDataArray.count)
        
        DispatchQueue.main.async {
            self.audioLevel = level
        }
        
        // Print audio samples to the console.
        let sampleValues = channelDataArray.map { String(format: "%.5f", $0) }
        print("[\(sampleValues.joined(separator: ", "))]")
        
        // Send samples to the FastAPI endpoint.
        sendSamplesToServer(samples: channelDataArray)
    }
    
    private func finalizeSamples() {
        guard let url = URL(string: finalizeString) else {
            print("Invalid finalize URL.")
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    
        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Error uploading samples: \(error)")
            } else if let httpResponse = response as? HTTPURLResponse,
                      httpResponse.statusCode != 200 {
                print("Server returned status code: \(httpResponse.statusCode)")
            } else {
                print("Successfully finalized.")
            }
        }
        
        task.resume()
    }
    
    /// Sends the given array of audio samples to the FastAPI /upload_samples endpoint.
    private func sendSamplesToServer(samples: [Float]) {
        guard let url = URL(string: uploadURLString) else {
            print("Invalid upload URL.")
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let jsonPayload: [String: Any] = ["samples": samples]
        
        do {
            let data = try JSONSerialization.data(withJSONObject: jsonPayload, options: [])
            request.httpBody = data
        } catch {
            print("Error converting samples to JSON: \(error)")
            return
        }
        
        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Error uploading samples: \(error)")
            } else if let httpResponse = response as? HTTPURLResponse,
                      httpResponse.statusCode != 200 {
                print("Server returned status code: \(httpResponse.statusCode)")
            } else {
                print("Successfully uploaded \(samples.count) samples.")
            }
        }
        
        task.resume()
    }
}

struct AudioProcessing_Preview: PreviewProvider {
    static var previews: some View {
        AudioProcessing()
    }
}
