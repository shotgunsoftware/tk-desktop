# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'desktop_window.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from sgtk.platform.qt import QtCore
for name, cls in QtCore.__dict__.items():
    if isinstance(cls, type): globals()[name] = cls

from sgtk.platform.qt import QtGui
for name, cls in QtGui.__dict__.items():
    if isinstance(cls, type): globals()[name] = cls


from ..action_list_view import ActionListView

from  . import resources_rc

class Ui_DesktopWindow(object):
    def setupUi(self, DesktopWindow):
        if not DesktopWindow.objectName():
            DesktopWindow.setObjectName(u"DesktopWindow")
        DesktopWindow.resize(427, 715)
        DesktopWindow.setMouseTracking(True)
        icon = QIcon()
        icon.addFile(u":/tk-desktop/default_systray_icon.png", QSize(), QIcon.Normal, QIcon.Off)
        DesktopWindow.setWindowIcon(icon)
        DesktopWindow.setDockNestingEnabled(False)
        DesktopWindow.setUnifiedTitleAndToolBarOnMac(False)
        self.actionQuit = QAction(DesktopWindow)
        self.actionQuit.setObjectName(u"actionQuit")
        self.actionQuit.setShortcutVisibleInContextMenu(True)
        self.actionPin_to_Menu = QAction(DesktopWindow)
        self.actionPin_to_Menu.setObjectName(u"actionPin_to_Menu")
        self.actionSign_Out = QAction(DesktopWindow)
        self.actionSign_Out.setObjectName(u"actionSign_Out")
        self.actionKeep_on_Top = QAction(DesktopWindow)
        self.actionKeep_on_Top.setObjectName(u"actionKeep_on_Top")
        self.actionKeep_on_Top.setCheckable(True)
        self.actionProject_Filesystem_Folder = QAction(DesktopWindow)
        self.actionProject_Filesystem_Folder.setObjectName(u"actionProject_Filesystem_Folder")
        self.actionShow_Console = QAction(DesktopWindow)
        self.actionShow_Console.setObjectName(u"actionShow_Console")
        self.actionRefresh_Projects = QAction(DesktopWindow)
        self.actionRefresh_Projects.setObjectName(u"actionRefresh_Projects")
        self.actionAdvanced_Project_Setup = QAction(DesktopWindow)
        self.actionAdvanced_Project_Setup.setObjectName(u"actionAdvanced_Project_Setup")
        self.actionHelp = QAction(DesktopWindow)
        self.actionHelp.setObjectName(u"actionHelp")
        self.actionRegenerate_Certificates = QAction(DesktopWindow)
        self.actionRegenerate_Certificates.setObjectName(u"actionRegenerate_Certificates")
        self.center = QWidget(DesktopWindow)
        self.center.setObjectName(u"center")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.center.sizePolicy().hasHeightForWidth())
        self.center.setSizePolicy(sizePolicy)
        self.center.setMouseTracking(True)
        self.border_layout = QVBoxLayout(self.center)
        self.border_layout.setSpacing(0)
        self.border_layout.setObjectName(u"border_layout")
        self.border_layout.setContentsMargins(0, 0, 0, 0)
        self.banners = QWidget(self.center)
        self.banners.setObjectName(u"banners")
        self.banners.setAutoFillBackground(True)
        self.verticalLayout_4 = QVBoxLayout(self.banners)
        self.verticalLayout_4.setSpacing(1)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)

        self.border_layout.addWidget(self.banners)

        self.header = QFrame(self.center)
        self.header.setObjectName(u"header")
        self.header.setFrameShape(QFrame.NoFrame)
        self.header.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.header)
        self.horizontalLayout_2.setSpacing(20)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(20, 0, 20, 0)
        self.tabs = QHBoxLayout()
        self.tabs.setObjectName(u"tabs")

        self.horizontalLayout_2.addLayout(self.tabs)

        self.header_spacer_5 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.header_spacer_5)

        self.border_layout.addWidget(self.header)

        self.tab_view = QStackedWidget(self.center)
        self.tab_view.setObjectName(u"tab_view")
        self.apps_tab = QStackedWidget()
        self.apps_tab.setObjectName(u"apps_tab")
        self.project_browser_page = QWidget()
        self.project_browser_page.setObjectName(u"project_browser_page")
        self.verticalLayout = QVBoxLayout(self.project_browser_page)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.subheader = QFrame(self.project_browser_page)
        self.subheader.setObjectName(u"subheader")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.subheader.sizePolicy().hasHeightForWidth())
        self.subheader.setSizePolicy(sizePolicy1)
        self.subheader.setMaximumSize(QSize(16777215, 60))
        self.subheader.setFrameShape(QFrame.NoFrame)
        self.subheader.setFrameShadow(QFrame.Plain)
        self.subheader.setLineWidth(1)
        self.subheader.setMidLineWidth(0)
        self.horizontalLayout = QHBoxLayout(self.subheader)
        self.horizontalLayout.setSpacing(15)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(20, 15, 15, 15)
        self.subheader_label = QLabel(self.subheader)
        self.subheader_label.setObjectName(u"subheader_label")
        self.subheader_label.setMouseTracking(True)
        self.subheader_label.setFocusPolicy(Qt.WheelFocus)
        self.subheader_label.setTextInteractionFlags(Qt.NoTextInteraction)

        self.horizontalLayout.addWidget(self.subheader_label)

        self.spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.spacer)

        self.search_frame = QFrame(self.subheader)
        self.search_frame.setObjectName(u"search_frame")
        self.search_frame.setFrameShape(QFrame.StyledPanel)
        self.search_frame.setFrameShadow(QFrame.Raised)
        self.search_frame.setProperty("collapsed", False)
        self.horizontalLayout_6 = QHBoxLayout(self.search_frame)
        self.horizontalLayout_6.setSpacing(2)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(5, 5, 5, 5)
        self.search_magnifier = QLabel(self.search_frame)
        self.search_magnifier.setObjectName(u"search_magnifier")
        sizePolicy2 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.search_magnifier.sizePolicy().hasHeightForWidth())
        self.search_magnifier.setSizePolicy(sizePolicy2)
        self.search_magnifier.setMaximumSize(QSize(17, 17))
        self.search_magnifier.setPixmap(QPixmap(u":/tk-desktop/search_dark.png"))
        self.search_magnifier.setScaledContents(True)

        self.horizontalLayout_6.addWidget(self.search_magnifier)

        self.search_text = QLineEdit(self.search_frame)
        self.search_text.setObjectName(u"search_text")

        self.horizontalLayout_6.addWidget(self.search_text)

        self.search_button = QPushButton(self.search_frame)
        self.search_button.setObjectName(u"search_button")
        sizePolicy2.setHeightForWidth(self.search_button.sizePolicy().hasHeightForWidth())
        self.search_button.setSizePolicy(sizePolicy2)
        self.search_button.setMaximumSize(QSize(17, 17))
        self.search_button.setFocusPolicy(Qt.NoFocus)
        icon1 = QIcon()
        icon1.addFile(u":/tk-desktop/icon_inbox_clear.png", QSize(), QIcon.Normal, QIcon.Off)
        self.search_button.setIcon(icon1)
        self.search_button.setIconSize(QSize(17, 17))
        self.search_button.setFlat(True)

        self.horizontalLayout_6.addWidget(self.search_button)

        self.horizontalLayout.addWidget(self.search_frame)

        self.verticalLayout.addWidget(self.subheader)

        self.projects = ActionListView(self.project_browser_page)
        self.projects.setObjectName(u"projects")
        sizePolicy3 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.projects.sizePolicy().hasHeightForWidth())
        self.projects.setSizePolicy(sizePolicy3)
        self.projects.setMouseTracking(True)
        self.projects.setFocusPolicy(Qt.NoFocus)
        self.projects.setFrameShape(QFrame.NoFrame)
        self.projects.setFrameShadow(QFrame.Plain)
        self.projects.setLineWidth(0)
        self.projects.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.projects.setAutoScroll(False)
        self.projects.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.projects.setProperty("showDropIndicator", False)
        self.projects.setSelectionMode(QAbstractItemView.SingleSelection)
        self.projects.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.projects.setMovement(QListView.Static)
        self.projects.setFlow(QListView.LeftToRight)
        self.projects.setProperty("isWrapping", True)
        self.projects.setResizeMode(QListView.Adjust)
        self.projects.setLayoutMode(QListView.SinglePass)
        self.projects.setSpacing(5)
        self.projects.setViewMode(QListView.IconMode)
        self.projects.setUniformItemSizes(False)
        self.projects.setSelectionRectVisible(False)

        self.verticalLayout.addWidget(self.projects)

        self.apps_tab.addWidget(self.project_browser_page)
        self.project_page = QWidget()
        self.project_page.setObjectName(u"project_page")
        self.verticalLayout_2 = QVBoxLayout(self.project_page)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.project_subheader = QFrame(self.project_page)
        self.project_subheader.setObjectName(u"project_subheader")
        sizePolicy.setHeightForWidth(self.project_subheader.sizePolicy().hasHeightForWidth())
        self.project_subheader.setSizePolicy(sizePolicy)
        self.project_subheader.setMaximumSize(QSize(16777215, 60))
        self.project_subheader.setFrameShape(QFrame.NoFrame)
        self.project_subheader.setFrameShadow(QFrame.Plain)
        self.project_subheader.setLineWidth(1)
        self.project_subheader.setMidLineWidth(0)
        self.horizontalLayout_4 = QHBoxLayout(self.project_subheader)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.spacer_button_1 = QPushButton(self.project_subheader)
        self.spacer_button_1.setObjectName(u"spacer_button_1")
        sizePolicy4 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.spacer_button_1.sizePolicy().hasHeightForWidth())
        self.spacer_button_1.setSizePolicy(sizePolicy4)
        self.spacer_button_1.setMinimumSize(QSize(10, 0))
        self.spacer_button_1.setMaximumSize(QSize(10, 16777215))
        self.spacer_button_1.setBaseSize(QSize(10, 0))
        self.spacer_button_1.setFocusPolicy(Qt.NoFocus)
        self.spacer_button_1.setFlat(True)

        self.horizontalLayout_4.addWidget(self.spacer_button_1)

        self.project_arrow = QPushButton(self.project_subheader)
        self.project_arrow.setObjectName(u"project_arrow")
        self.project_arrow.setMaximumSize(QSize(30, 62))
        self.project_arrow.setFocusPolicy(Qt.NoFocus)
        icon2 = QIcon()
        icon2.addFile(u":/tk-desktop/back_arrow.png", QSize(), QIcon.Normal, QIcon.Off)
        self.project_arrow.setIcon(icon2)
        self.project_arrow.setIconSize(QSize(20, 20))
        self.project_arrow.setFlat(True)

        self.horizontalLayout_4.addWidget(self.project_arrow)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_2)

        self.project_icon = QLabel(self.project_subheader)
        self.project_icon.setObjectName(u"project_icon")
        sizePolicy5 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.project_icon.sizePolicy().hasHeightForWidth())
        self.project_icon.setSizePolicy(sizePolicy5)
        self.project_icon.setMaximumSize(QSize(42, 42))
        self.project_icon.setPixmap(QPixmap(u":/tk-desktop/missing_thumbnail_project.png"))
        self.project_icon.setScaledContents(True)
        self.project_icon.setMargin(5)

        self.horizontalLayout_4.addWidget(self.project_icon)

        self.project_name = QLabel(self.project_subheader)
        self.project_name.setObjectName(u"project_name")
        sizePolicy6 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.project_name.sizePolicy().hasHeightForWidth())
        self.project_name.setSizePolicy(sizePolicy6)
        self.project_name.setMaximumSize(QSize(280, 16777215))
        self.project_name.setMargin(5)

        self.horizontalLayout_4.addWidget(self.project_name)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_3)

        self.project_menu = QToolButton(self.project_subheader)
        self.project_menu.setObjectName(u"project_menu")
        self.project_menu.setFocusPolicy(Qt.NoFocus)
        icon3 = QIcon()
        icon3.addFile(u":/tk-desktop/down_arrow.png", QSize(), QIcon.Normal, QIcon.Off)
        self.project_menu.setIcon(icon3)
        self.project_menu.setIconSize(QSize(20, 20))
        self.project_menu.setPopupMode(QToolButton.InstantPopup)

        self.horizontalLayout_4.addWidget(self.project_menu)

        self.spacer_button_4 = QPushButton(self.project_subheader)
        self.spacer_button_4.setObjectName(u"spacer_button_4")
        sizePolicy4.setHeightForWidth(self.spacer_button_4.sizePolicy().hasHeightForWidth())
        self.spacer_button_4.setSizePolicy(sizePolicy4)
        self.spacer_button_4.setMinimumSize(QSize(10, 0))
        self.spacer_button_4.setMaximumSize(QSize(10, 16777215))
        self.spacer_button_4.setBaseSize(QSize(10, 0))
        self.spacer_button_4.setFocusPolicy(Qt.NoFocus)
        self.spacer_button_4.setFlat(True)

        self.horizontalLayout_4.addWidget(self.spacer_button_4)

        self.verticalLayout_2.addWidget(self.project_subheader)

        self.configuration_frame = QFrame(self.project_page)
        self.configuration_frame.setObjectName(u"configuration_frame")
        self.configuration_frame.setFrameShape(QFrame.NoFrame)
        self.configuration_frame.setFrameShadow(QFrame.Plain)
        self.horizontalLayout_8 = QHBoxLayout(self.configuration_frame)
        self.horizontalLayout_8.setSpacing(0)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.horizontalSpacer = QSpacerItem(150, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer)

        self.configuration_name = QLabel(self.configuration_frame)
        self.configuration_name.setObjectName(u"configuration_name")
        self.configuration_name.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_8.addWidget(self.configuration_name)

        self.configuration_label = QLabel(self.configuration_frame)
        self.configuration_label.setObjectName(u"configuration_label")
        self.configuration_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_8.addWidget(self.configuration_label)

        self.horizontalLayout_8.setStretch(0, 1)
        self.horizontalLayout_8.setStretch(1, 1)
        self.horizontalLayout_8.setStretch(2, 1)

        self.verticalLayout_2.addWidget(self.configuration_frame)

        self.command_panel_area = QScrollArea(self.project_page)
        self.command_panel_area.setObjectName(u"command_panel_area")
        self.command_panel_area.setStyleSheet(u"QScrollArea {\n"
"border: 0, 0, 0, 0\n"
"}")
        self.command_panel_area.setWidgetResizable(True)
        self.command_panel_area.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.scrollAreaWidgetContents_3 = QWidget()
        self.scrollAreaWidgetContents_3.setObjectName(u"scrollAreaWidgetContents_3")
        self.scrollAreaWidgetContents_3.setGeometry(QRect(0, 0, 100, 30))
        self.command_panel_area.setWidget(self.scrollAreaWidgetContents_3)

        self.verticalLayout_2.addWidget(self.command_panel_area)

        self.apps_tab.addWidget(self.project_page)
        self.tab_view.addWidget(self.apps_tab)

        self.border_layout.addWidget(self.tab_view)

        self.footer = QFrame(self.center)
        self.footer.setObjectName(u"footer")
        self.footer.setMouseTracking(True)
        self.footer.setFrameShape(QFrame.NoFrame)
        self.footer.setFrameShadow(QFrame.Plain)
        self.horizontalLayout_3 = QHBoxLayout(self.footer)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(10, 5, 10, 5)
        self.shotgun_button = QPushButton(self.footer)
        self.shotgun_button.setObjectName(u"shotgun_button")
        sizePolicy7 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.shotgun_button.sizePolicy().hasHeightForWidth())
        self.shotgun_button.setSizePolicy(sizePolicy7)
        self.shotgun_button.setMinimumSize(QSize(132, 26))
        self.shotgun_button.setMaximumSize(QSize(132, 26))
        self.shotgun_button.setMouseTracking(True)
        self.shotgun_button.setFocusPolicy(Qt.NoFocus)
        icon4 = QIcon()
        icon4.addFile(u":/tk-desktop/shotgun_logo_light_medium.png", QSize(), QIcon.Normal, QIcon.Off)
        self.shotgun_button.setIcon(icon4)
        self.shotgun_button.setIconSize(QSize(122, 16))
        self.shotgun_button.setFlat(True)

        self.horizontalLayout_3.addWidget(self.shotgun_button)

        self.footer_spacer = QSpacerItem(173, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.footer_spacer)

        self.user_button = QPushButton(self.footer)
        self.user_button.setObjectName(u"user_button")
        sizePolicy2.setHeightForWidth(self.user_button.sizePolicy().hasHeightForWidth())
        self.user_button.setSizePolicy(sizePolicy2)
        self.user_button.setMinimumSize(QSize(40, 40))
        self.user_button.setMaximumSize(QSize(40, 40))
        self.user_button.setMouseTracking(True)
        self.user_button.setFocusPolicy(Qt.NoFocus)
        icon5 = QIcon()
        icon5.addFile(u":/tk-desktop/default_user_thumb.png", QSize(), QIcon.Normal, QIcon.Off)
        self.user_button.setIcon(icon5)
        self.user_button.setIconSize(QSize(30, 30))
        self.user_button.setFlat(True)

        self.horizontalLayout_3.addWidget(self.user_button)

        self.border_layout.addWidget(self.footer)

        DesktopWindow.setCentralWidget(self.center)
        QWidget.setTabOrder(self.projects, self.user_button)
        QWidget.setTabOrder(self.user_button, self.search_button)
        QWidget.setTabOrder(self.search_button, self.search_text)

        self.retranslateUi(DesktopWindow)

        self.apps_tab.setCurrentIndex(0)

        QMetaObject.connectSlotsByName(DesktopWindow)
    # setupUi

    def retranslateUi(self, DesktopWindow):
        DesktopWindow.setWindowTitle(QCoreApplication.translate("DesktopWindow", u"Flow Production Tracking", None))
        self.actionQuit.setText(QCoreApplication.translate("DesktopWindow", u"Quit", None))
#if QT_CONFIG(tooltip)
        self.actionQuit.setToolTip(QCoreApplication.translate("DesktopWindow", u"Quit", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.actionQuit.setShortcut(QCoreApplication.translate("DesktopWindow", u"Ctrl+Q", None))
#endif // QT_CONFIG(shortcut)
        self.actionPin_to_Menu.setText(QCoreApplication.translate("DesktopWindow", u"Pin to Menu", None))
        self.actionSign_Out.setText(QCoreApplication.translate("DesktopWindow", u"Sign Out", None))
        self.actionKeep_on_Top.setText(QCoreApplication.translate("DesktopWindow", u"Keep on Top", None))
        self.actionProject_Filesystem_Folder.setText(QCoreApplication.translate("DesktopWindow", u"Project Filesystem Folder", None))
        self.actionShow_Console.setText(QCoreApplication.translate("DesktopWindow", u"Show Console", None))
#if QT_CONFIG(tooltip)
        self.actionShow_Console.setToolTip(QCoreApplication.translate("DesktopWindow", u"Show the logging console.", None))
#endif // QT_CONFIG(tooltip)
        self.actionRefresh_Projects.setText(QCoreApplication.translate("DesktopWindow", u"Refresh Projects", None))
#if QT_CONFIG(tooltip)
        self.actionRefresh_Projects.setToolTip(QCoreApplication.translate("DesktopWindow", u"Refreshes the project information.", None))
#endif // QT_CONFIG(tooltip)
        self.actionAdvanced_Project_Setup.setText(QCoreApplication.translate("DesktopWindow", u"Advanced project setup...", None))
#if QT_CONFIG(tooltip)
        self.actionAdvanced_Project_Setup.setToolTip(QCoreApplication.translate("DesktopWindow", u"Launch the classic project setup wizard", None))
#endif // QT_CONFIG(tooltip)
        self.actionHelp.setText(QCoreApplication.translate("DesktopWindow", u"Help", None))
        self.actionRegenerate_Certificates.setText(QCoreApplication.translate("DesktopWindow", u"Regenerate Certificates", None))
#if QT_CONFIG(tooltip)
        self.actionRegenerate_Certificates.setToolTip(QCoreApplication.translate("DesktopWindow", u"Regenerates browser integration certificates", None))
#endif // QT_CONFIG(tooltip)
        self.subheader_label.setText(QCoreApplication.translate("DesktopWindow", u"PROJECTS", None))
#if QT_CONFIG(tooltip)
        self.search_frame.setToolTip(QCoreApplication.translate("DesktopWindow", u"Search Projects", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.search_magnifier.setToolTip(QCoreApplication.translate("DesktopWindow", u"Search Projects", None))
#endif // QT_CONFIG(tooltip)
        self.search_magnifier.setText("")
#if QT_CONFIG(tooltip)
        self.search_text.setToolTip(QCoreApplication.translate("DesktopWindow", u"Search Projects", None))
#endif // QT_CONFIG(tooltip)
        self.search_text.setPlaceholderText(QCoreApplication.translate("DesktopWindow", u"Search Projects", None))
#if QT_CONFIG(tooltip)
        self.search_button.setToolTip(QCoreApplication.translate("DesktopWindow", u"Clear search", None))
#endif // QT_CONFIG(tooltip)
        self.search_button.setText("")
        self.spacer_button_1.setText("")
#if QT_CONFIG(tooltip)
        self.project_arrow.setToolTip(QCoreApplication.translate("DesktopWindow", u"Back to Projects", None))
#endif // QT_CONFIG(tooltip)
        self.project_arrow.setText("")
        self.project_icon.setText("")
        self.project_name.setText(QCoreApplication.translate("DesktopWindow", u"Project", None))
#if QT_CONFIG(tooltip)
        self.project_menu.setToolTip(QCoreApplication.translate("DesktopWindow", u"Project Menu", None))
#endif // QT_CONFIG(tooltip)
        self.spacer_button_4.setText("")
        self.configuration_name.setText(QCoreApplication.translate("DesktopWindow", u"Configuration Name", None))
        self.configuration_label.setText(QCoreApplication.translate("DesktopWindow", u"CONFIGURATION", None))
#if QT_CONFIG(tooltip)
        self.shotgun_button.setToolTip(QCoreApplication.translate("DesktopWindow", u"Open in Flow Production Tracking", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.user_button.setToolTip(QCoreApplication.translate("DesktopWindow", u"User menu", None))
#endif // QT_CONFIG(tooltip)
        self.user_button.setText("")
    # retranslateUi
