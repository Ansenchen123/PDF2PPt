import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    width: 1180
    height: 760
    minimumWidth: 980
    minimumHeight: 640
    visible: true
    title: "PDF2PPt Studio"
    color: "#F4F6F8"

    property int pageEnd: appController.totalPages > 0 ? appController.totalPages : 1

    FontLoader { id: inter; source: "" }

    header: ToolBar {
        height: 58
        background: Rectangle { color: "#111827" }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 18
            anchors.rightMargin: 18
            spacing: 14
            Label {
                text: "PDF2PPt Studio"
                color: "#F9FAFB"
                font.pixelSize: 18
                font.bold: true
                Layout.alignment: Qt.AlignVCenter
            }
            Rectangle { width: 1; height: 24; color: "#334155" }
            Label {
                text: appController.status
                color: "#CBD5E1"
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
            ProgressBar {
                value: appController.progress / 100
                visible: appController.busy || appController.progress > 0
                Layout.preferredWidth: 180
            }
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 18

        Rectangle {
            Layout.preferredWidth: 360
            Layout.fillHeight: true
            radius: 8
            color: "#FFFFFF"
            border.color: "#D7DEE8"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 14

                Label { text: "Input"; font.pixelSize: 15; font.bold: true; color: "#111827" }
                Button {
                    text: "Select PDF"
                    Layout.fillWidth: true
                    enabled: !appController.busy
                    onClicked: appController.selectPdf()
                }
                TextField {
                    text: appController.pdfPath
                    readOnly: true
                    placeholderText: "No PDF selected"
                    Layout.fillWidth: true
                }

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Pages"; color: "#475569" }
                    SpinBox { id: startPage; from: 1; to: Math.max(1, appController.totalPages); value: 1; enabled: !appController.busy }
                    Label { text: "to"; color: "#475569" }
                    SpinBox { id: endPage; from: 1; to: Math.max(1, appController.totalPages); value: window.pageEnd; enabled: !appController.busy }
                }

                Rectangle { height: 1; color: "#E5EAF0"; Layout.fillWidth: true }

                Label { text: "Model"; font.pixelSize: 15; font.bold: true; color: "#111827" }
                ComboBox {
                    id: providerCombo
                    model: ["gemini", "openai", "anthropic", "mistral", "mock"]
                    Layout.fillWidth: true
                    enabled: !appController.busy
                    onCurrentTextChanged: apiKey.text = appController.loadApiKey(currentText)
                }
                ComboBox {
                    id: authModeCombo
                    model: [
                        { text: "Use my API key", value: "byok" },
                        { text: "Managed proxy", value: "proxy" }
                    ]
                    textRole: "text"
                    valueRole: "value"
                    Layout.fillWidth: true
                    enabled: !appController.busy
                }

                StackLayout {
                    Layout.fillWidth: true
                    currentIndex: authModeCombo.currentIndex
                    ColumnLayout {
                        TextField {
                            id: apiKey
                            echoMode: TextInput.Password
                            placeholderText: providerCombo.currentText + " API key"
                            text: appController.loadApiKey(providerCombo.currentText)
                            Layout.fillWidth: true
                        }
                        Button {
                            text: "Save key"
                            enabled: apiKey.text.length > 0 && !appController.busy
                            Layout.fillWidth: true
                            onClicked: appController.saveApiKey(providerCombo.currentText, apiKey.text)
                        }
                    }
                    ColumnLayout {
                        TextField {
                            id: proxyUrl
                            placeholderText: "Proxy URL"
                            text: appController.proxyUrl
                            Layout.fillWidth: true
                            onTextChanged: appController.updateProxy(proxyUrl.text, proxyToken.text)
                        }
                        TextField {
                            id: proxyToken
                            echoMode: TextInput.Password
                            placeholderText: "Proxy token"
                            text: appController.proxyToken
                            Layout.fillWidth: true
                            onTextChanged: appController.updateProxy(proxyUrl.text, proxyToken.text)
                        }
                    }
                }

                Rectangle { height: 1; color: "#E5EAF0"; Layout.fillWidth: true }

                Label { text: "Output"; font.pixelSize: 15; font.bold: true; color: "#111827" }
                RowLayout {
                    Layout.fillWidth: true
                    TextField {
                        id: outputPath
                        text: appController.outputPath
                        placeholderText: "Output .pptx path"
                        Layout.fillWidth: true
                    }
                    Button {
                        text: "Browse"
                        enabled: !appController.busy
                        onClicked: appController.selectOutput()
                    }
                }

                Item { Layout.fillHeight: true }

                Button {
                    text: "Start conversion"
                    Layout.fillWidth: true
                    highlighted: true
                    enabled: !appController.busy
                    onClicked: appController.startConversion(
                        providerCombo.currentText,
                        authModeCombo.currentValue,
                        startPage.value,
                        endPage.value,
                        apiKey.text,
                        outputPath.text
                    )
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 8
            color: "#FFFFFF"
            border.color: "#D7DEE8"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 14

                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: "Workspace"
                        font.pixelSize: 15
                        font.bold: true
                        color: "#111827"
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        text: "Open output folder"
                        enabled: appController.lastOutput.length > 0
                        onClicked: appController.openOutputFolder()
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 6
                    color: "#F8FAFC"
                    border.color: "#E2E8F0"

                    ColumnLayout {
                        anchors.centerIn: parent
                        width: Math.min(parent.width - 80, 520)
                        spacing: 12
                        Label {
                            text: appController.pdfPath.length > 0 ? "Ready to reconstruct editable slides" : "Select a PDF to begin"
                            horizontalAlignment: Text.AlignHCenter
                            font.pixelSize: 22
                            font.bold: true
                            color: "#0F172A"
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                        }
                        Label {
                            text: appController.totalPages > 0 ? appController.totalPages + " pages loaded" : "Provider, page range, and output controls are on the left."
                            horizontalAlignment: Text.AlignHCenter
                            color: "#64748B"
                            font.pixelSize: 14
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                        }
                        ProgressBar {
                            value: appController.progress / 100
                            visible: appController.busy
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }
    }
}
