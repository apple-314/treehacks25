//
import SwiftUI

@main
struct visionprotestApp: App {
    var body: some Scene {
        WindowGroup {
//            ContentView()
//            AudioProcessing()
            TabView {
                ConversationalPage()
                    .tabItem {
                        Image(systemName: "speaker.wave.3")
                        Text("Audio")
                    }
                    .background(.clear)
                HistoryView()
                    .tabItem {
                        Image(systemName: "list.bullet")
                        Text("History")
                    }
                    .background(.clear)

            }
        }
        .windowStyle(.plain)
        .defaultSize(width: .infinity, height: .infinity)

    }
}
