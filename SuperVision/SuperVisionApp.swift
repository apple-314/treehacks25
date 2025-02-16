//
//  SuperVisionApp.swift
//  SuperVision
//
//  Created by Aarav Wattal on 2/15/25.
//

import SwiftUI

@main
struct SuperVisionApp: App {
    var body: some Scene {
        WindowGroup {
            TabView {
                ConversationPage()
                    .tabItem {
                        Image(systemName: "speaker.wave.3")
                        Text("Audio")
                    }
                    .background(.clear)
                HistoryPage()
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
