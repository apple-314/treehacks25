import SwiftUI
import AVFoundation

// MARK: - API Response Models

struct Profile: Codable {
    let about: String
    let education: [[String]]
    let experiences: [[String]]
    let profile_url: String
        
    // Optional computed properties to format the arrays for display
    var educationText: String {
        education.map { $0.joined(separator: " - ") }.joined(separator: "\n")
    }
    
    var experiencesText: String {
        experiences.map { $0.joined(separator: " - ") }.joined(separator: "\n")
    }
}

struct CaptureResponse: Codable {
    let message: String
    let screenshot: String
    let profile: Profile
}


struct AudioProcessing: View {
    @StateObject private var audioProcessor = AudioProcessor()
    
    @State private var profile: Profile? = nil

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                
                HStack {
                    VStack(alignment: .leading) {
                        if let profile = profile {
                            ProfileDescriptionView(
                                about: profile.about,
                                education: profile.educationText,
                                experiences: profile.experiencesText,
                                profileURL: profile.profile_url
                            )
                        } else {
                            // A placeholder view until data is available.
                            Text("No profile data available.\nTap the capture button to load profile.")
                                .foregroundColor(.black)
                                .font(.system(size: 24, weight: .medium))
                                .padding()
                        }
                        Spacer()
                    }
                    Spacer()
                }
                
                HStack {
                    Spacer()
                    VStack {
                        Spacer()
                        Button(action: {
                            print("Taking a picture of the person")

                            NetworkManager.captureGesture { result in
                                switch result {
                                case .success(let profileData):
                                    DispatchQueue.main.async {
                                        self.profile = profileData
                                    }
                                case .failure(let error):
                                    print("Error capturing gesture: \(error)")
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
    let about: String
    let education: String
    let experiences: String
    let profileURL: String
    
    var body: some View {
        GeometryReader { geometry in
            VStack(alignment: .leading, spacing: 8) {
                Text(about)
                    .foregroundColor(.black)
                    .font(.custom("BricolageGrotesque-96ptExtraBold_Bold", size: 45))
                    .padding(.bottom, 5)
                
                Text("Education")
                    .foregroundColor(.black)
                    .font(.custom("BricolageGrotesque-96ptExtraBold_SemiBold", size: 30))
                
                Text(education)
                    .foregroundColor(.black)
                    .font(.custom("BricolageGrotesque-96ptExtraBold_Light", size: 30))
                    .padding(.leading, 20)
                
                Text("Experiences")
                    .foregroundColor(.black)
                    .font(.system(size: 30, weight: .semibold, design: .default))
                
                ForEach(experiences.components(separatedBy: "\n"), id: \.self) { exp in
                    DisclosureGroup {
                        Text(exp)
                            .foregroundColor(.black)
                            .font(.custom("BricolageGrotesque-96ptExtraBold_Light", size: 20))
                            .padding(.leading, 13)
                    } label: {
                        Text(exp)
                            .foregroundColor(.black)
                            .font(.custom("BricolageGrotesque-96ptExtraBold_Light", size: 30))
                    }
                    .foregroundColor(.black)
                }
                
                Text("Profile URL: \(profileURL)")
                    .foregroundColor(.blue)
                    .underline()
            }
            .frame(width: 500)
            .padding(40)
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
        
        let directory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let fileName = "recording.wav"
        let fileURL = directory.appendingPathComponent(fileName)
        self.fileURL = fileURL
        
        do {
            if FileManager.default.fileExists(atPath: fileURL.path) {
                try FileManager.default.removeItem(at: fileURL)
            }
            audioFile = try AVAudioFile(forWriting: fileURL,
                                        settings: format.settings,
                                        commonFormat: .pcmFormatFloat32,
                                        interleaved: false)
            print("Audio file will be saved at: \(fileURL.path)")
        } catch {
            print("Error creating audio file: \(error)")
            return
        }
        
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
        let level = channelDataArray.map { abs($0) }.reduce(0, +) / Float(channelDataArray.count)
        
        DispatchQueue.main.async {
            self.audioLevel = level
        }
        
        let sampleValues = channelDataArray.map { String(format: "%.5f", $0) }
        print("[\(sampleValues.joined(separator: ", "))]")
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
                print("Error finalizing samples: \(error)")
            } else if let httpResponse = response as? HTTPURLResponse,
                      httpResponse.statusCode != 200 {
                print("Server returned status code: \(httpResponse.statusCode)")
            } else {
                print("Successfully finalized.")
            }
        }
        task.resume()
    }
    
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
            r = 255; g = 255; b = 255; a = 255
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}
