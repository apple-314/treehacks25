import SwiftUI
import AVFoundation

struct AudioProcessing: View {
    @StateObject private var audioProcessor = AudioProcessor()
    
    var body: some View {
        VStack {
            Text("Audio Processing")
                .font(.largeTitle)
                .padding()
            
            // Display audio level as a bar
            RoundedRectangle(cornerRadius: 10)
                .fill(Color.blue)
                .frame(width: CGFloat(audioProcessor.audioLevel) * 200, height: 30)
                .animation(.easeInOut, value: audioProcessor.audioLevel)
                .padding()
            
            Button(audioProcessor.isRecording ? "Stop" : "Start") {
                audioProcessor.isRecording ? audioProcessor.stopRecording() : audioProcessor.startRecording()
            }
            .padding()
            .background(audioProcessor.isRecording ? Color.red : Color.green)
            .foregroundColor(.white)
            .cornerRadius(10)
        }
        .onAppear {
            audioProcessor.setupAudioSession()
        }
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
    
    // Set this to the URL of your FastAPI endpoint.
    private let uploadURLString = "http://127.0.0.1:8000/upload_samples"
    
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
        self.fileURL = fileURL  // Save for later printing
        
        do {
            // Remove an existing file if necessary
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
        
        // Install tap to process audio and write to file
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
    }
    
    private func processAudio(buffer: AVAudioPCMBuffer) {
        guard let channelData = buffer.floatChannelData?[0] else { return }
        let channelDataArray = Array(UnsafeBufferPointer(start: channelData,
                                                         count: Int(buffer.frameLength)))
        // Compute average audio level
        let level = channelDataArray.map { abs($0) }.reduce(0, +) / Float(channelDataArray.count)
        
        DispatchQueue.main.async {
            self.audioLevel = level
        }
        
        // Print every audio sample to the console.
        let sampleValues = channelDataArray.map { String(format: "%.5f", $0) }
        print("📊 Audio Samples: [\(sampleValues.joined(separator: ", "))]")
        
        // Send samples to the FastAPI endpoint.
        sendSamplesToServer(samples: channelDataArray)
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
