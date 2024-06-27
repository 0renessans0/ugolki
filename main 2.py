import sys
import time
import random
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, \
    QGraphicsRectItem, QVBoxLayout, QWidget, QPushButton, QMessageBox, QStackedWidget, QLabel, QHBoxLayout, QSlider
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QPen, QBrush, QPixmap, QIcon


class Piece(QGraphicsEllipseItem):
    def __init__(self, board, x, y, color):
        super().__init__(-board.tile_size / 2, -board.tile_size / 2, board.tile_size - 2, board.tile_size - 2)
        self.board = board
        self.setPos(x * board.tile_size + board.tile_size / 2, y * board.tile_size + board.tile_size / 2)
        self.setBrush(QBrush(color))
        self.position = (x, y)
        self.mouse_down = False
        self.setFlags(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    def mousePressEvent(self, event):
        self.board.clearMoveIndicators()

        if event.button() == Qt.MouseButton.LeftButton:
            self.board.showMoves(self)

        event.ignore()

    def move(self, x, y):
        self.setPos(x * self.board.tile_size + self.board.tile_size / 2,
                    y * self.board.tile_size + self.board.tile_size / 2)
        self.position = (int(x), int(y))


class MoveIndicator(QGraphicsRectItem):
    def __init__(self, x, y, board, piece):
        super().__init__(0, 0, board.tile_size, board.tile_size)
        self.setPos(x * board.tile_size, y * board.tile_size)
        self.setBrush(QBrush(Qt.GlobalColor.green))
        self.piece = piece
        self.board = board

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            new_x = int(self.x() / self.board.tile_size)
            new_y = int(self.y() / self.board.tile_size)
            new_position = (new_x, new_y)
            if (0 <= new_x < self.board.board_size and
                    0 <= new_y < self.board.board_size and
                    self.board.isFree(new_position)):
                self.board.movePiece(self.piece, new_position)
            self.board.clearMoveIndicators()


class Board(QGraphicsView):
    def __init__(self, color1, color2, app, game_instance, difficulty='hard'):
        super().__init__()
        self.app = app
        self.scene = QGraphicsScene()
        self.game_instance = game_instance
        self.setScene(self.scene)
        self.board_size = 8
        self.move_count = 0
        self.color1 = color1
        self.color2 = color2
        self.color_names = {
            Qt.GlobalColor.black: "Черные",
            Qt.GlobalColor.white: "Белые",
            Qt.GlobalColor.red: "Красные",
            Qt.GlobalColor.yellow: "Желтые",
        }
        self.player = QSoundEffect()
        self.winner = QSoundEffect()
        self.current_player = color2
        self.difficulty = difficulty
        self.black = 0
        self.white = 0
        self.volumeSlider = QSlider(Qt.Orientation.Horizontal)
        self.volumeSlider.setStyleSheet("""
                QSlider::groove:horizontal {
                    height: 8px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #bbdefb, stop:1 #0d47a1);
                    margin: 2px 0;
                }
                QSlider::handle:horizontal {
                    background: #0d47a1;
                    border: 1px solid #0d47a1;
                    width: 18px;
                    margin: -2px 0; 
                    border-radius: 9px;
                }
                QSlider::add-page:horizontal {
                    background: #5c6bc0;
                }
                QSlider::sub-page:horizontal {
                    background: #bbdefb;
                }
                """)
        self.volumeSlider.setMinimum(0)
        self.level_selection_widget = None
        self.sound_effect = QSoundEffect()
        self.sound_effect.setSource(QUrl.fromLocalFile("click.wav"))
        self.volumeSlider.setMaximum(100)
        self.volumeSlider.setValue(50)
        self.volumeSlider.setTickPosition(QSlider.TickPosition.TicksAbove)
        self.volumeSlider.valueChanged.connect(self.player.setVolume)
        self.tile_size = 100
        self.pieces = []
        self.initUI()

    def initUI(self):
        self.horizontalLayout = QHBoxLayout()
        self.controlPanelWidget = QWidget()
        self.controlPanelLayout = QVBoxLayout()
        self.setStyleSheet("""
            QGraphicsView {
                background: lightgray;
                border-radius: 34px; 
            }
        """)
        color_name_1 = self.color_names.get(self.color1)
        color_name_2 = self.color_names.get(self.color2)
        self.scoreLabel = QLabel(f"Счет: {color_name_1} - {self.black}, {color_name_2} - {self.white}")
        self.restartButton = QPushButton("Начать сначала")
        self.backButton = QPushButton("Передать ход")

        self.controlPanelLayout.addWidget(self.scoreLabel)
        self.controlPanelLayout.addWidget(self.restartButton)
        self.controlPanelLayout.addWidget(self.backButton)
        self.controlPanelWidget.setLayout(self.controlPanelLayout)
        self.volumeSliderLayout = QVBoxLayout()
        self.volumeSliderLayout.addWidget(self.volumeSlider)
        self.controlPanelLayout.insertLayout(0, self.volumeSliderLayout)
        self.horizontalLayout.addWidget(self)
        self.horizontalLayout.addWidget(self.controlPanelWidget)
        self.backgroundMusic = QSoundEffect()
        self.backgroundMusic.setSource(QUrl.fromLocalFile("522.wav"))
        self.backgroundMusic.setVolume(0.5)
        self.backgroundMusic.setLoopCount(-2)
        self.backgroundMusic.play()
        self.volumeSlider.valueChanged.connect(self.setVolume)
        mainLayoutWidget = QWidget()
        mainLayoutWidget.setLayout(self.horizontalLayout)
        self.app.setCentralWidget(mainLayoutWidget)

        self.drawBoard()
        self.placePieces()
        self.player.setSource(QUrl.fromLocalFile("20.wav"))
        self.winner.setSource(QUrl.fromLocalFile("52.wav"))

        # Привязываем обработчики событий к кнопкам
        self.restartButton.clicked.connect(self.resetGame)
        self.backButton.clicked.connect(self.changePlayer)

    def checkWinCondition(self):
        self.difficulty = 'classic'
        color1_in_home = 0
        color2_in_home = 0

        for piece in self.pieces:
            if self.isInOppositeCorner(piece.position, piece.brush().color()):
                if piece.brush().color() == self.color1:
                    color1_in_home += 1
                elif piece.brush().color() == self.color2:
                    color2_in_home += 1

        if color1_in_home == 9:
            return self.color1
        elif color2_in_home == 9:
            return self.color2
        return None

    def checkMediumCondition(self):
        self.difficulty = 'medium'
        color1_in_target = 0
        color2_in_target = 0

        target_positions_color1 = [(x, y) for y in range(self.board_size - 3, self.board_size) for x in
                                   range(self.board_size - 4, self.board_size)]
        target_positions_color2 = [(x, y) for y in range(3) for x in range(4)]

        for piece in self.pieces:
            piece_position = piece.position
            piece_color = piece.brush().color()

            if piece_color == self.color1 and piece_position in target_positions_color1:
                color1_in_target += 1
            elif piece_color == self.color2 and piece_position in target_positions_color2:
                color2_in_target += 1

        if color1_in_target == 1:
            return self.color1
        elif color2_in_target == 1:
            return self.color2
        return None

    def getValidMoves(self, piece):
        moves = self.getValidJumps(piece)
        x, y = piece.position
        for dx in [-1, 1]:
            if 0 <= x + dx < self.board_size and self.isFree((x + dx, y)):
                moves.append((x + dx, y))
            if 0 <= y + dx < self.board_size and self.isFree((x, y + dx)):
                moves.append((x, y + dx))

        return moves

    def getValidJumps(self, piece):
        jumps = []
        x, y = piece.position
        for d in [-2, 2]:
            if 0 <= x + d < self.board_size:
                mid_x = x + d // 2
                if self.getPieceAt(mid_x, y) and self.isFree((x + d, y)):
                    jumps.append((x + d, y))
            if 0 <= y + d < self.board_size:
                mid_y = y + d // 2
                if self.getPieceAt(x, mid_y) and self.isFree((x, y + d)):
                    jumps.append((x, y + d))
        return jumps

    def showMoves(self, piece):
        if piece.brush().color() != self.current_player:
            return
        self.clearMoveIndicators()
        moves = self.getValidMoves(piece)
        for move in moves:
            if self.isFree(move):
                indicator = MoveIndicator(move[0], move[1], self, piece)
                self.scene.addItem(indicator)

    def movePiece(self, piece, new_pos):
        if self.getPieceAt(new_pos[0], new_pos[1]) is None and piece.brush().color() == self.current_player:
            piece.move(new_pos[0], new_pos[1])
            piece.position = new_pos
            if self.isInOppositeCorner(piece.position, piece.brush().color()):
                if piece.brush().color() == self.color1:
                    self.black += 1
                else:
                    self.white += 1
            if self.current_player == self.color2:
                self.current_player = self.color1
                self.white += 1
                self.updateStatusBar()
                QTimer.singleShot(0, self.player.play)
            else:
                self.current_player = self.color2
                self.black += 1
                self.updateStatusBar()
                QTimer.singleShot(0, self.player.play)
            self.move_count += 1
            if self.move_count >= 80:
                self.declareDraw()
                return
        if self.difficulty == 'classic':
            winner = self.checkWinCondition()
        elif self.difficulty == 'medium':
            winner = self.checkMediumCondition()
        else:
            winner = self.checkHardCondition()
        if winner:
            self.declareWinner(winner)

    def declareDraw(self):
        msg = QMessageBox()
        msg.setWindowTitle("Ничья!")
        msg.setText("Игра закончилась ничьей из-за превышения количества ходов.")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        answer = msg.exec()
        if answer == QMessageBox.StandardButton.Ok:
            self.resetGame()

    def checkHardCondition(self):
        self.difficulty = 'hard'
        start_diagonal = 4
        color1_in_target_positions = 0
        color2_in_target_positions = 0

        target_positions_color1 = [(x, y) for y in range(self.board_size) for x in range(self.board_size) if
                                   x + y >= self.board_size + start_diagonal - 2]
        target_positions_color2 = [(x, y) for y in range(self.board_size) for x in range(self.board_size) if
                                   x + y <= self.board_size - start_diagonal]

        for piece in self.pieces:
            piece_position = piece.position
            piece_color = piece.brush().color()

            if piece_color == self.color1 and piece_position in target_positions_color1:
                color1_in_target_positions += 1
            elif piece_color == self.color2 and piece_position in target_positions_color2:
                color2_in_target_positions += 1

        if color1_in_target_positions == 15:
            return self.color1
        elif color2_in_target_positions == 15:
            return self.color2

        return None

    def declareWinner(self, winner_color):
        self.player.stop()
        self.winner.play()
        winner = "Первый игрок" if winner_color == self.color1 else "Второй игрок"
        msg = QMessageBox()
        msg.setWindowTitle("Победа!")
        msg.setText(f"{winner} победили!")
        msg.setInformativeText(f"Хотите начать новую игру?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        answer = msg.exec()

        if answer == QMessageBox.StandardButton.Yes:
            self.resetGame()
        else:
            sys.exit(0)

    def resetGame(self):
        self.black = 0
        self.white = 0
        self.current_player = self.color2
        self.clearBoard()
        self.initBoardWithDifficulty()
        self.updateStatusBar()

    def initBoardWithDifficulty(self):
        positions_color1 = []
        positions_color2 = []

        if self.difficulty == 'classic':
            for y in range(3):
                for x in range(3):
                    positions_color1.append((x, y))
                    positions_color2.append((self.board_size - 1 - x, self.board_size - 1 - y))
        elif self.difficulty == 'medium':
            for y in range(3):
                for x in range(4):
                    positions_color1.append((x, y))
                    positions_color2.append((self.board_size - 1 - x, self.board_size - 1 - y))
        else:
            start_diagonal = 4
            for y in range(self.board_size):
                for x in range(self.board_size):
                    if x + y <= self.board_size - start_diagonal:
                        positions_color1.append((x, y))
                    elif x + y >= self.board_size + start_diagonal - 2:
                        positions_color2.append((x, y))

        self.placePiecesWithPositions(positions_color1, self.color1)
        self.placePiecesWithPositions(positions_color2, self.color2)

    def placePiecesWithPositions(self, positions, color):
        for position in positions:
            self.create_piece(position, color)

    def clearBoard(self):
        for piece in self.pieces:
            self.scene.removeItem(piece)
        self.pieces.clear()

    def isFree(self, pos):
        return self.getPieceAt(*pos) is None

    def changePlayer(self):
        if self.current_player == self.color1:
            self.black += 1
        else:
            self.white += 1
        self.current_player = self.color1 if self.current_player == self.color2 else self.color2
        self.move_count += 1
        self.updateStatusBar()
        if self.move_count >= 80:
            self.declareDraw()

    def getPieceAt(self, x, y):
        for piece in self.pieces:
            if piece.position == (x, y):
                return piece
        return None

    def updateStatusBar(self):
        color_name_1 = self.color_names.get(self.color1)
        color_name_2 = self.color_names.get(self.color2)
        self.statusText = f"Счет: {color_name_1} - {self.black}, {color_name_2} - {self.white}"
        self.scoreLabel.setText(self.statusText)

    def drawBoard(self):
        self.scene.clear()
        for x in range(self.board_size):
            for y in range(self.board_size):
                color = Qt.GlobalColor.gray if (x + y) % 2 == 0 else Qt.GlobalColor.lightGray
                self.scene.addRect(x * self.tile_size, y * self.tile_size,
                                   self.tile_size, self.tile_size,
                                   QPen(Qt.GlobalColor.black), color)

    def placePieces(self):
        for y in range(3):
            for x in range(3):
                self.create_piece((x, y), self.color1)
                self.create_piece((self.board_size - 1 - x, self.board_size - 1 - y), self.color2)

    def create_piece(self, position, color):
        piece = Piece(self, position[0], position[1], color)
        self.pieces.append(piece)
        self.scene.addItem(piece)

    def clearMoveIndicators(self):
        for item in list(self.scene.items()):
            if isinstance(item, MoveIndicator):
                self.scene.removeItem(item)

    def isInOppositeCorner(self, position, color):
        x, y = position
        if color == self.color1:
            return x >= self.board_size - 3 and y >= self.board_size - 3
        else:
            return x < 3 and y < 3

    def setVolume(self, value):
        volumeLevel = value / 100
        self.player.setVolume(volumeLevel)
        self.backgroundMusic.setVolume(volumeLevel)


class Game(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 1000, 900)
        self.setMinimumWidth(1690)
        self.setMinimumHeight(900)
        self.setStyleSheet("""
            QMainWindow {
                background: QLinearGradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #8e44ad, stop:1 #3498db);
            }
            QPushButton {
                font-size: 20px; 
                background-color: rgba(255, 255, 255, 0.8);
                border: 2px solid #ecf0f1;
                border-radius: 20px; 
                padding: 20px; 
                color: #2c3e50;
                font-weight: bold;
                text-transform: uppercase;
                min-width: 220px; 
                min-height: 60px; 

            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 1);
            }
            QPushButton:pressed {
                background-color: #bdc3c7;
            }
            QLabel {
                font-size: 28px; /* Больше размер шрифта для лейбла */
                color: #ecf0f1;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-weight: bold; /* Жирный шрифт */
                margin-bottom: 20px;
            }
        """)
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        self.setWindowTitle("Уголки")

        self.menu_widget = QWidget()
        self.menu_layout = QVBoxLayout()

        self.sound_effect = QSoundEffect()
        self.sound_effect.setSource(QUrl.fromLocalFile("click.wav"))

        self.play_button = QPushButton("Играть")
        self.options_button = QPushButton("Правила")
        self.exit_button = QPushButton("Выход")
        self.title_label = QLabel("Игра Уголки")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.menu_layout.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignCenter)
        self.menu_layout.addSpacing(30)
        buttons = [self.play_button, self.options_button, self.exit_button]
        for button in buttons:
            button.setFixedSize(200, 50)
            self.menu_layout.addWidget(button, 0, Qt.AlignmentFlag.AlignCenter)
            self.menu_layout.addSpacing(50)
        self.menu_widget.setLayout(self.menu_layout)

        self.initRulesWidget()
        self.initColorSelectionWidget()

        self.central_widget.addWidget(self.menu_widget)
        self.central_widget.addWidget(self.color_selection_widget)
        self.central_widget.addWidget(self.rules_widget)

        self.play_button.clicked.connect(self.openColorSelection)
        self.classic_colors_button.clicked.connect(
            lambda: self.openPositionChoice(Qt.GlobalColor.black, Qt.GlobalColor.white))
        self.custom_colors_button.clicked.connect(
            lambda: self.openPositionChoice(Qt.GlobalColor.red, Qt.GlobalColor.yellow))
        self.rules_back_button.clicked.connect(self.goToMainMenu1)
        self.options_button.clicked.connect(self.goToRules)
        self.exit_button.clicked.connect(self.closeGame)

    def initRulesWidget(self):
        self.rules_widget = QWidget()
        self.rules_layout = QVBoxLayout()
        self.rules_layout.addStretch()

        self.rules_text = QLabel("Правила игры:\n\n"
                                 "Цель игры - переместить все свои фишки в противоположный угол доски.\n"
                                 "Игроки ходят по очереди, перемещая одну из своих фишек на свободную соседнюю клетку.\n"
                                 "Фишки могут перемещаться на клетку вперёд, назад, влево или вправо, но не по диагонали.\n"
                                 "Если игрок не может сделать ход, он пропускает ход.\n"
                                 "Игра заканчивается, когда все фишки одного из игроков оказываются в противоположном углу.")
        self.rules_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rules_layout.addWidget(self.rules_text)

        self.rules_layout.addStretch()

        back_button_layout = QHBoxLayout()
        self.setupBackButton(back_button_layout, self.goToMainMenu1)
        self.rules_layout.addLayout(back_button_layout)
        self.rules_widget.setLayout(self.rules_layout)

    def initColorSelectionWidget(self):
        self.color_selection_widget = QWidget()
        self.color_selection_layout = QVBoxLayout()

        self.classic_colors_button = QPushButton("Черные и Белые")
        self.custom_colors_button = QPushButton("Красные и Желтые")

        self.color_selection_layout.addWidget(self.classic_colors_button, 2, Qt.AlignmentFlag.AlignCenter)
        self.color_selection_layout.addWidget(self.custom_colors_button, 1, Qt.AlignmentFlag.AlignCenter)

        self.color_selection_layout.addStretch()

        back_button_layout = QHBoxLayout()

        self.setupBackButton(back_button_layout, lambda: self.central_widget.setCurrentWidget(self.menu_widget))

        self.color_selection_layout.addLayout(back_button_layout)

        self.color_selection_widget.setLayout(self.color_selection_layout)

    def closeGame(self):
        self.playSoundEffect()
        time.sleep(0.1)
        sys.exit(0)

    def goToMainMenu1(self):
        self.playSoundEffect()
        self.central_widget.setCurrentWidget(self.menu_widget)

    def goToRules(self):
        self.playSoundEffect()
        self.central_widget.setCurrentWidget(self.rules_widget)

    def playSoundEffect(self):
        self.sound_effect.play()

    def openColorSelection(self):
        self.playSoundEffect()
        self.central_widget.setCurrentWidget(self.color_selection_widget)

    def openPositionChoice(self, color1, color2):
        self.playSoundEffect()
        position_choice_widget = QWidget()
        main_layout = QVBoxLayout()

        header_label = QLabel("Выберите уровень сложности")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addStretch()
        buttons_layout = QHBoxLayout()
        classic_position_button = self.createLevelButton("Легкий")
        random_position_button = self.createLevelButton("Средний")
        custom_position_button = self.createLevelButton("Сложный")

        buttons_layout.addWidget(classic_position_button)
        buttons_layout.addWidget(random_position_button)
        buttons_layout.addWidget(custom_position_button)

        buttons_centered_layout = QVBoxLayout()
        buttons_centered_layout.addLayout(buttons_layout)
        buttons_centered_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(header_label)
        main_layout.addLayout(buttons_centered_layout)

        main_layout.addStretch()

        back_button_layout = QHBoxLayout()
        self.setupBackButton(back_button_layout, self.openColorSelection)
        main_layout.addLayout(back_button_layout)

        position_choice_widget.setLayout(main_layout)
        self.central_widget.addWidget(position_choice_widget)
        self.central_widget.setCurrentWidget(position_choice_widget)

        classic_position_button.clicked.connect(
            lambda: self.startGame(color1, color2, 'classic'))
        random_position_button.clicked.connect(
            lambda: self.startGame(color1, color2, 'medium'))
        custom_position_button.clicked.connect(
            lambda: self.startGame(color1, color2, 'hard'))

    def startGame(self, color1, color2, difficulty):
        self.playSoundEffect()
        self.board_size = 8
        positions_color1 = []
        positions_color2 = []

        if difficulty == 'classic':
            for y in range(3):
                for x in range(3):
                    positions_color1.append((x, y))
                    positions_color2.append((self.board_size - 1 - x, self.board_size - 1 - y))
        elif difficulty == 'medium':
            for y in range(3):
                for x in range(4):
                    positions_color1.append((x, y))
                    positions_color2.append((self.board_size - 1 - x, self.board_size - 1 - y))
        else:
            start_diagonal = 4
            for y in range(self.board_size):
                for x in range(self.board_size):
                    if x + y <= self.board_size - start_diagonal:
                        positions_color1.append((x, y))
                    elif x + y >= self.board_size + start_diagonal - 2:
                        positions_color2.append((x, y))

        self.openGameBoard(color1, color2, positions_color1, positions_color2, difficulty)

    def openGameBoard(self, color1, color2, positions_color1, positions_color2, difficulty):
        board = Board(color1, color2, self, self, difficulty)
        board.pieces = []
        board.drawBoard()
        for position in positions_color1:
            board.create_piece(position, color1)
        for position in positions_color2:
            board.create_piece(position, color2)

        self.central_widget.setCurrentWidget(board)

    def createLevelButton(self, text):
        button = QPushButton()
        button_layout = QVBoxLayout()

        button.setMinimumHeight(150)
        button.setMaximumWidth(100)

        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
                font-size: 20px; 
                color: #2c3e50;
                font-weight: bold;
                text-transform: uppercase;
                min-width: 220px; 
                min-height: 60px;
        """)

        button_layout.addWidget(label)

        button.setLayout(button_layout)

        return button

    def setupBackButton(self, layout, callback):
        self.rules_back_button = QPushButton("← Назад")
        self.rules_back_button.setStyleSheet("""
                    QPushButton {
                        font-size: 16px;
                        border: 2px solid #7f8c8d;
                        border-radius: 10px;
                        padding: 10px;
                        background: #ecf0f1;
                    }
                    QLabel {
                        font-size: 20px;
                        color: #2c3e50;
                    }
                """)
        layout.addWidget(self.rules_back_button, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.rules_back_button.clicked.connect(callback)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = Game()
    game.show()
    app.exec()
