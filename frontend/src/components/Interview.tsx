import { useState } from 'react'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import Box from '@mui/material/Box'
import CircularProgress from '@mui/material/CircularProgress'
import Divider from '@mui/material/Divider'

type Props = {
  photoId: string
  analysisResult: Record<string, unknown>
  questions: string[]
  nextQuestion: string | null
  qaHistory: { question: string; answer: string }[]
  onAnswer: (question: string, answer: string) => void
  loading: boolean
  /** 单张照片最大对话轮数（问题 x / maxRounds） */
  maxRounds?: number
}

const DEFAULT_MAX_ROUNDS = 10

export default function Interview({
  photoId,
  analysisResult,
  questions,
  nextQuestion,
  qaHistory,
  onAnswer,
  loading,
  maxRounds = DEFAULT_MAX_ROUNDS,
}: Props) {
  const [answer, setAnswer] = useState('')
  const currentQ = nextQuestion ?? questions[qaHistory.length] ?? null
  const currentIndex = qaHistory.length + 1

  const handleSubmit = () => {
    const a = answer.trim()
    if (!currentQ || !a) return
    onAnswer(currentQ, a)
    setAnswer('')
  }

  const desc = analysisResult?.overall_description as string | undefined
  const summary = desc ? (typeof desc === 'string' ? desc.slice(0, 300) : String(desc).slice(0, 300)) : ''

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        访谈对话
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        照片：{photoId}
      </Typography>
      {summary && (
        <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.100', borderRadius: 2 }}>
          <Typography variant="caption" color="text.secondary">分析摘要</Typography>
          <Typography variant="body2" sx={{ mt: 0.5 }}>{summary}…</Typography>
        </Box>
      )}
      <Divider sx={{ my: 2 }} />
      {currentQ ? (
        <>
          <Typography variant="subtitle1" fontWeight={600} gutterBottom>
            问题 {currentIndex} / {maxRounds}
          </Typography>
          <Typography sx={{ mb: 2 }}>{currentQ}</Typography>
          <TextField
            fullWidth
            multiline
            minRows={3}
            placeholder="请输入您的回答"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            disabled={loading}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSubmit()
              }
            }}
          />
          <Button
            variant="contained"
            sx={{ mt: 2 }}
            onClick={handleSubmit}
            disabled={loading || !answer.trim()}
            startIcon={loading ? <CircularProgress size={18} color="inherit" /> : undefined}
          >
            {loading ? '提交中…' : '提交回答'}
          </Button>
        </>
      ) : (
        <Typography color="text.secondary">暂无新问题，请在上一步选择「完成并生成故事」或「添加下一张照片」。</Typography>
      )}
      {qaHistory.length > 0 && (
        <>
          <Divider sx={{ my: 2 }} />
          <Typography variant="caption" color="text.secondary">已收集 {qaHistory.length} 组问答</Typography>
        </>
      )}
    </Paper>
  )
}
