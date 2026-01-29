import { useRef } from 'react'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Box from '@mui/material/Box'
import CircularProgress from '@mui/material/CircularProgress'
import CloudUpload from '@mui/icons-material/CloudUpload'

type Props = {
  mode: 'single' | 'multi'
  multiPhotoCount: number
  onAnalyze: (file: File) => void
  onFinishMulti: () => void
  loading: boolean
  showGenerateOnly?: boolean
  onGenerateStory?: () => void
}

export default function UploadAnalyze({
  mode,
  multiPhotoCount,
  onAnalyze,
  onFinishMulti,
  loading,
  showGenerateOnly,
  onGenerateStory,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && file.type.startsWith('image/')) {
      onAnalyze(file)
    }
    e.target.value = ''
  }

  if (showGenerateOnly && onGenerateStory) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography gutterBottom>访谈已结束，点击下方生成故事</Typography>
        <Button
          variant="contained"
          size="large"
          onClick={onGenerateStory}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} color="inherit" /> : undefined}
        >
          {loading ? '生成中…' : '生成故事'}
        </Button>
      </Paper>
    )
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        {mode === 'multi' ? '添加照片' : '上传照片'}
      </Typography>
      {mode === 'multi' && multiPhotoCount > 0 && (
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          当前共 {multiPhotoCount} 张。可继续添加或稍后在访谈结束后选择「完成并生成多图故事」。
        </Typography>
      )}
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        onChange={handleFile}
        style={{ display: 'none' }}
      />
      <Button
        variant="outlined"
        size="large"
        fullWidth
        startIcon={loading ? <CircularProgress size={20} /> : <CloudUpload />}
        onClick={() => inputRef.current?.click()}
        disabled={loading}
        sx={{ py: 3 }}
      >
        {loading ? '分析中…' : '选择图片上传并分析'}
      </Button>
    </Paper>
  )
}
