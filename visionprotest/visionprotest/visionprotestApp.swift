//
import SwiftUI

@main
struct visionprotestApp: App {
    var body: some Scene {
        WindowGroup {
<<<<<<< HEAD
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
=======
            ContentView()
//            AudioProcessing()
>>>>>>> aaa0e8989485401348d08f45075b63a296c2a197
        }
        .windowStyle(.plain)
        .defaultSize(width: .infinity, height: .infinity)

    }
}
