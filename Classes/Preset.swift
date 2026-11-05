//
//  Preset.swift
//  Subler
//
//  Created by Damiano Galassi on 21/08/2017.
//

import Foundation

protocol Preset: NSSecureCoding, NSCopying {
    var title: String { get set }
    var changed: Bool { get set }
    var version: Int { get }

    var pathExtension: String { get }
}

extension Preset {

    private func appSupportURL() -> URL? {
        return FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first.map({ AppIdentity.supportURL(in: $0) })
    }

    var fileURL: URL {
        guard let url = appSupportURL() else { fatalError() }
        return url.appendingPathComponent(title).appendingPathExtension(pathExtension)
    }
}
