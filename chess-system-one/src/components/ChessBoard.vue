<script setup lang="ts">
import { TheChessboard } from 'vue3-chessboard';
import { ref } from 'vue'
import { BoardApi, type BoardConfig, type MoveableColor } from 'vue3-chessboard';
import type { PieceColor, SquareKey } from 'vue3-chessboard';
import 'vue3-chessboard/style.css';

const props = defineProps<{
    systemOneServerConfig: {
        baseUrl: string,
        bearerToken?: string,
        model?: string
    }
}>()


const boardConfig = ref<BoardConfig>({})
const playerToMove = ref<MoveableColor>('both');
const boardApi = ref<BoardApi>();

const evaluation = ref({
    score: 0,
    label: 'balanced',
});
const isWinning = ref();
const winner = ref();


const COLOR_NAME = {
    'w': 'white',
    'b': 'black'
}

const PIECE_SYMBOL_NAME = {
    'p': 'pawn',
    'n': 'knight',
    'b': 'bishop',
    'r': 'rook',
    'q': 'queen',
    'k': 'king',
}


function buildCriteriaFromUnplayedMove(
    move: {from: SquareKey, to: SquareKey}
) {
    const key = `${move.from}-${move.to}`;

    const sourcePiece = boardApi.value?.getSquare(move.from);
    const targetPiece = boardApi.value?.getSquare(move.to);

    const fragments = ['Move'];

    if (sourcePiece) {
        fragments.push(`${COLOR_NAME[sourcePiece.color]} ${PIECE_SYMBOL_NAME[sourcePiece.type]}`);
    }
    fragments.push(`from ${move.from} to ${move.to}.`)
    if (targetPiece) {
        fragments.push(`This move captures ${COLOR_NAME[targetPiece.color]} ${PIECE_SYMBOL_NAME[targetPiece.type]}`);
    }

    const description = fragments.join(" ");
    
    return [key, description]
}



async function getBestMove(fen: string, moves: {from: SquareKey, to: SquareKey}[]) {
    const body = {
        model: props.systemOneServerConfig.model || 'von-latest',
        state: {
            fen
        },
        questions: {
            next_best_move: {
                type: 'choice',
                instructions: 'Given the current state of the chess game in FEN notation, choose your next best move from the provided list of available moves.',
                criteria: Object.fromEntries(moves.map(buildCriteriaFromUnplayedMove))
            },
            positional_evaluation: {
                type: 'score',
                instructions: 'Is this position good for you or bad for you?',
                criteria: [
                    "extremely_bad: Almost guaranteed to lose this game",
                    "unfavourable_but_playable: While not really a winnable position, may be able to hold.",
                    "balanced: About equal position, so any side could win.",
                    "good: There is significant advantage, that can be converted into a win.",
                    "extremely_good: Almost guaranteed to win this game",
                ]
            },
            is_the_position_winnable: {
                type: 'noul',
                instructions: "Determine whether you're winning the game."
            }
        }
    }
    // console.log("Built body", body);

    const url = `${props.systemOneServerConfig.baseUrl}/v1/systemone`;

    const headers: any = {
        'Content-Type': 'application/json',
    }
    if (props.systemOneServerConfig.bearerToken) {
        headers['Authorization'] = `Bearer ${props.systemOneServerConfig.bearerToken}`;
    }

    const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(body)
    })
    // console.log("Response raw", response);
    const responseBody = (await response.json());
    // console.log(`ResponseBody: ${JSON.stringify(responseBody)}`);

    const nextBestMoveString: string = responseBody.answers.next_best_move.choice;
    const positionalEvaluation: number = responseBody.answers.positional_evaluation.score;
    const positionalEvalIdx: number = Math.round(positionalEvaluation);
    const positionalEvalLabel: string = body.questions.positional_evaluation.criteria[positionalEvalIdx];
    const isWinning: number = responseBody.answers.is_the_position_winnable.noul;

    const [src, dest] = nextBestMoveString.split("-", 2);
    return {
        move: {
            from: src,
            to: dest,
        },
        evaluation: {
            score: -(positionalEvaluation - 2),
            label: positionalEvalLabel,
        },
        is_winning: isWinning >= 0.5
    }
}

function onBoardCreated(api: BoardApi) {
    boardApi.value = api;
}

const OPPONENT_COLOR = 'b';

function onBoardMove(move: any) {
    // console.log("Move happened!", move);

    // Do nothing if the opponent moved.
    if (move.color == OPPONENT_COLOR) {
        return;
    }

    // we moved. so get the next best move.
    const possibleMoves = 
        boardApi.value?.getPossibleMoves();

    const moves: {from: SquareKey, to: SquareKey}[] = [];

    possibleMoves?.forEach((targetSquares, sourceSquare) => {
        targetSquares.forEach((targetSquare) => {
            moves.push({
                from: sourceSquare as SquareKey,
                to: targetSquare as SquareKey
            });
        })
    }) 

    const currentFen: string | undefined = boardApi.value?.getFen();

    // console.log("moves", possibleMoves, "currentFen", currentFen);

    // console.log("Getting best moves")
    getBestMove(currentFen as string, moves)
    .then((bestMove) => {
        // console.log("Got best move; Playing.", bestMove);
        if (boardApi.value?.move({from: bestMove.move.from as SquareKey, to: bestMove.move.to as SquareKey})) {
            // console.log("move played!");
            isWinning.value = bestMove.is_winning;
            evaluation.value = bestMove.evaluation;
        } else {
            console.error("invalid move.");
        }
    });
}

function onCheckMate(color: PieceColor) {
    console.log(`${color} got checkmated!`);
    switch (color) {
        case 'black':
            winner.value = 'white';
            break
        case 'white':
            winner.value = 'black';
            break
    }
}

function resetGame() {
    winner.value = null;
    isWinning.value = null;
    evaluation.value = {
        label: 'balanced',
        score: 0,
    }
    boardApi.value?.resetBoard();
}

</script>
<template>
    <div style="width: 80%; height: auto; display: flex; flex-direction: column; justify-content: center; align-items: center;">
        <h5 v-if="winner == 'white'">
            You beat "{{ systemOneServerConfig.model }}" System-One Model!
        </h5>
        <h5 v-else-if="winner == 'black'">
            You lost to "{{ systemOneServerConfig.model }}"! :sadge:
        </h5>
        <TheChessboard 
            :board-config="boardConfig" 
            :reactive-config="true"
            :player-color="playerToMove"
            @board-created="onBoardCreated"
            @checkmate="onCheckMate"
            @move="onBoardMove"
        />
        <small>
            Evaluation: {{ evaluation.score.toFixed(3) }}, Label: {{  evaluation.label }}
        </small>
        <button style="width: 300px; height: auto; margin: 0 auto; margin-top: 24px;" @click="resetGame">Restart Game</button>
        </div>
</template>