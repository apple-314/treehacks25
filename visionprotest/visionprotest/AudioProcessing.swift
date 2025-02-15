import SwiftUI
import AVFoundation

struct AudioProcessing: View {
    @StateObject private var audioProcessor = AudioProcessor()
    
    // Example multiline description text.
    let name = "Isaac Newton"
    let headline = "Scientist / Physicist"
    let experiences = """
    Principal • Menlo Ventures
    Engineering Fellow • Kleiner Perkins
    Engineering Fellow • Kleiner Perkins
    """
    let experienceDescription = "Experience Description Example Experience Description Example Experience Description Example Experience Description Example Experience Description Example Example"
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                
                HStack {
                    VStack(alignment: .leading) {
                        ProfileDescriptionView(name: name, headline: headline, experiences: experiences, experienceDescription: experienceDescription)
                        Spacer()
                    }
                    Spacer()
                }
                
                
                HStack {
                    Spacer()
                    VStack {
                        Spacer()
                        Button(action: {
                            print("taking picture of person")
                            for family in UIFont.familyNames.sorted() {
                                print("Family: \(family)")
                                for name in UIFont.fontNames(forFamilyName: family).sorted() {
                                    print("  - \(name)")
                                }
                            }
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

struct ProfileDescriptionView: View {
    let name: String
    let headline: String
    let experiences: String
    let experienceDescription: String
    var bulletPoints: [String] {
        experiences.components(separatedBy: "\n").filter { !$0.isEmpty }
    }

    var body: some View {
        GeometryReader { geometry in
            VStack(alignment: .leading, spacing: 8) {
                
                Text(name)
                    .foregroundColor(.black)
                    .font(.custom("BricolageGrotesque-96ptExtraBold_Bold", size: 45))
                    .padding(.bottom, 5)
                
                Text("Headline")
                    .foregroundColor(.black)
                    .font(.custom("BricolageGrotesque-96ptExtraBold_SemiBold", size: 30))
                
                Text(headline)
                    .foregroundColor(.black)
                    .font(.custom("BricolageGrotesque-96ptExtraBold_Light", size: 30))
                    .padding(.leading, 20)
                
                Text("Experiences")
                    .foregroundColor(.black)
                    .font(.system(size: 30, weight: .semibold, design: .default))
                
                
                ForEach(bulletPoints, id: \.self) { statement in
                    DisclosureGroup {
                        
                        Text(experienceDescription)
                            .foregroundColor(.black)
                            .font(.custom("BricolageGrotesque-96ptExtraBold_Light", size: 20))
                            .padding(.leading, 13)
                            
                    } label: {
                        Text(statement)
                            .foregroundColor(.black)
                            .font(.custom("BricolageGrotesque-96ptExtraBold_Light", size: 30))
                    }
                    .foregroundColor(.black)
                }
            }
            .frame(width: 500)
            .padding(.top, 40)
            .padding(.trailing, 40)
            .padding(.bottom, 40)
            .padding(.leading, 25)
            .background(
                RoundedRectangle(cornerRadius: 30)
                    .fill(Color(hex: "E2E2E2E2").opacity(0.6))
            )
        }
    }
}

class AudioProcessor: ObservableObject {
    private var audioEngine = AVAudioEngine()
    private var inputNode: AVAudioInputNode?
    private var audioFormat: AVAudioFormat?
    private var isAudioSessionConfigured = false
    private var audioFile: AVAudioFile?
    private var fileURL: URL?
    
    @Published var isRecording = false
    @Published var audioLevel: Float = 0.0
    
    
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


extension Color {

    init(hex: String) {
        
        let sanitizedHex = hex
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .replacingOccurrences(of: "#", with: "")

        
        var rgbValue: UInt64 = 0
        Scanner(string: sanitizedHex).scanHexInt64(&rgbValue)

        let r, g, b, a: UInt64
        switch sanitizedHex.count {
        case 6:
            r = (rgbValue >> 16) & 0xFF
            g = (rgbValue >> 8) & 0xFF
            b = rgbValue & 0xFF
            a = 0xFF
        case 8:
            r = (rgbValue >> 24) & 0xFF
            g = (rgbValue >> 16) & 0xFF
            b = (rgbValue >> 8) & 0xFF
            a = rgbValue & 0xFF
        default:
            r = 255
            g = 255
            b = 255
            a = 255
        }

        self.init(
            .sRGB,
            red:   Double(r) / 255,
            green: Double(g) / 255,
            blue:  Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}
