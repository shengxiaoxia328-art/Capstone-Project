import { useState, useCallback } from 'react'
import Box from '@mui/material/Box'
import Container from '@mui/material/Container'
import Typography from '@mui/material/Typography'
import Stepper from '@mui/material/Stepper'
import Step from '@mui/material/Step'
import StepLabel from '@mui/material/StepLabel'
import Paper from '@mui/material/Paper'
import ModeSelect from './components/ModeSelect'
import UploadAnalyze from './components/UploadAnalyze'
import Interview from './components/Interview'
import StoryResult from './components/StoryResult'
import ThinkingPanel from './components/ThinkingPanel'
import { api } from './api'

type Mode = 'single' | 'multi' | null

export default function App() {
  const [mode, setMode] = useState<Mode>(null)
  const [step, setStep] = useState<'mode' | 'upload' | 'interview' | 'multi_choice' | 'story'>('mode')
  const [analysis, setAnalysis] = useState<{
    photo_id: string
    analysis_result: Record<string, unknown>
    questions: string[]
  } | null>(null)
  const [qaHistory, setQaHistory] = useState<{ question: string; answer: string }[]>([])
  const [nextQuestion, setNextQuestion] = useState<string | null>(null)
  const [story, setStory] = useState<string | null>(null)
  const [multiPhotoCount, setMultiPhotoCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [thinkingLog, setThinkingLog] = useState<string[]>([])
  const [thinkingOpen, setThinkingOpen] = useState(true)
  const [streamingBuffer, setStreamingBuffer] = useState('')
  const [maxDialogueRounds, setMaxDialogueRounds] = useState(10)

  /** 思考过程最多保留 4 行，新的一行顶掉最上面一行（与对话思考样式一致） */
  const appendThinking = useCallback((text: string) => {
    setThinkingLog((prev) => {
      const next = [...prev, text]
      return next.length > 4 ? next.slice(-4) : next
    })
  }, [])
  const appendStreaming = useCallback((text: string) => {
    setStreamingBuffer((prev) => prev + text)
  }, [])
  const clearThinking = useCallback(() => {
    setThinkingLog([])
    setStreamingBuffer('')
  }, [])

  const handleModeSelect = async (m: 'single' | 'multi') => {
    setError(null)
    setLoading(true)
    try {
      const data = await api.init(m)
      setMode(m)
      setStep('upload')
      setAnalysis(null)
      setQaHistory([])
      setStory(null)
      setMultiPhotoCount(0)
      if (data && typeof (data as { max_dialogue_rounds?: number }).max_dialogue_rounds === 'number') {
        setMaxDialogueRounds((data as { max_dialogue_rounds: number }).max_dialogue_rounds)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '初始化失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyze = async (file: File) => {
    setError(null)
    setLoading(true)
    clearThinking()
    try {
      const data = await api.analyzeStream(file, appendThinking, appendStreaming)
      setAnalysis(data)
      setNextQuestion(data.questions?.[0] ?? null)
      setQaHistory([])
      setStep('interview')
    } catch (e) {
      setError(e instanceof Error ? e.message : '分析失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAnswer = async (question: string, answer: string) => {
    setError(null)
    setLoading(true)
    clearThinking()
    try {
      const data = await api.answerStream(question, answer, appendThinking, appendStreaming)
      setQaHistory(data.qa_history || [])
      const nq = data.next_question ?? null
      setNextQuestion(nq)
      if (!nq) {
        if (mode === 'multi') {
          const fin = await api.finishPhoto()
          setMultiPhotoCount(fin.photo_count ?? 1)
          setStep('multi_choice')
        } else {
          setStep('story')
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '提交失败')
    } finally {
      setLoading(false)
    }
  }

  const handleMultiChoiceAddPhoto = () => {
    setAnalysis(null)
    setQaHistory([])
    setNextQuestion(null)
    setStep('upload')
  }

  const handleGenerateStory = async () => {
    setError(null)
    setLoading(true)
    clearThinking()
    try {
      const data = await api.generateStoryStream(appendThinking, appendStreaming)
      setStory(data.story ?? '')
      setStep('story')
    } catch (e) {
      setError(e instanceof Error ? e.message : '生成故事失败')
    } finally {
      setLoading(false)
    }
  }

  const handleRestart = () => {
    setMode(null)
    setStep('mode')
    setStory(null)
    setAnalysis(null)
    setQaHistory([])
    clearThinking()
    api.setSessionId('')
  }

  const stepIndex = step === 'mode' ? 0 : step === 'upload' ? 1 : step === 'interview' || step === 'multi_choice' ? 2 : 3

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', py: 3 }}>
      <Container maxWidth="md">
        <Typography variant="h4" align="center" gutterBottom color="primary">
          照片的故事
        </Typography>
        <Typography variant="body2" align="center" color="text.secondary" sx={{ mb: 3 }}>
          视觉引导式访谈与叙事生成
        </Typography>

        <Stepper activeStep={stepIndex} sx={{ mb: 3 }}>
          <Step><StepLabel>选择模式</StepLabel></Step>
          <Step><StepLabel>上传照片</StepLabel></Step>
          <Step><StepLabel>访谈对话</StepLabel></Step>
          <Step><StepLabel>生成故事</StepLabel></Step>
        </Stepper>

        {error && (
          <Paper sx={{ p: 2, mb: 2, bgcolor: 'error.light', color: 'error.contrastText' }}>
            {error}
          </Paper>
        )}

        {step === 'mode' && (
          <ModeSelect onSelect={handleModeSelect} loading={loading} />
        )}

        {step === 'upload' && mode && (
          <UploadAnalyze
            mode={mode}
            multiPhotoCount={multiPhotoCount}
            onAnalyze={handleAnalyze}
            onFinishMulti={handleGenerateStory}
            loading={loading}
          />
        )}

        {step === 'interview' && analysis && (
          <Interview
            photoId={analysis.photo_id}
            analysisResult={analysis.analysis_result}
            questions={analysis.questions}
            nextQuestion={nextQuestion}
            qaHistory={qaHistory}
            onAnswer={handleAnswer}
            loading={loading}
            maxRounds={maxDialogueRounds}
          />
        )}

        {step === 'multi_choice' && mode === 'multi' && (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>本张照片访谈已结束</Typography>
            <Typography color="text.secondary" sx={{ mb: 2 }}>
              当前共 {multiPhotoCount} 张照片。可继续添加照片，或完成并生成多图故事。
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Box component="button" onClick={handleMultiChoiceAddPhoto} sx={{ px: 2, py: 1.5, borderRadius: 2, border: '1px solid', borderColor: 'primary.main', color: 'primary.main', bgcolor: 'transparent', cursor: 'pointer', fontWeight: 500 }}>
                添加下一张照片
              </Box>
              <Box component="button" onClick={handleGenerateStory} disabled={loading || multiPhotoCount < 2} sx={{ px: 2, py: 1.5, borderRadius: 2, bgcolor: 'primary.main', color: 'white', border: 'none', cursor: loading || multiPhotoCount < 2 ? 'not-allowed' : 'pointer', fontWeight: 500, opacity: multiPhotoCount < 2 ? 0.6 : 1 }}>
                {loading ? '生成中…' : '完成并生成多图故事'}
              </Box>
            </Box>
            {multiPhotoCount < 2 && (
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                至少需 2 张照片才能生成多图故事
              </Typography>
            )}
          </Paper>
        )}

        {step === 'story' && story !== null && (
          <StoryResult story={story} onRestart={handleRestart} />
        )}

        {step === 'story' && story === null && mode === 'single' && (
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography gutterBottom>正在生成故事…</Typography>
            <Box component="button" onClick={handleGenerateStory} disabled={loading} sx={{ mt: 2, px: 3, py: 1.5, borderRadius: 2, bgcolor: 'primary.main', color: 'white', border: 'none', cursor: loading ? 'not-allowed' : 'pointer' }}>
              {loading ? '生成中…' : '生成故事'}
            </Box>
          </Paper>
        )}

        <ThinkingPanel
          lines={thinkingLog}
          streamingText={streamingBuffer}
          open={thinkingOpen}
          onToggle={() => setThinkingOpen((o) => !o)}
        />
      </Container>
    </Box>
  )
}
