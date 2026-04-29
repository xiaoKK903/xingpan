import html2canvas from 'html2canvas'

export function sanitizeFilename(filename) {
  if (!filename) {
    const timestamp = new Date().toISOString().slice(0, 10)
    return `chart_${timestamp}`
  }
  
  let result = String(filename)
  
  result = result.replace(/[<>:"/\\|?*\x00-\x1f]/g, '_')
  
  result = result.replace(/[<>:"/\\|?*]/g, '_')
  
  result = result.replace(/\s+/g, '_')
  
  result = result.replace(/_+/g, '_')
  
  result = result.replace(/^_+|_+$/g, '')
  
  if (!result || result.length === 0) {
    const timestamp = new Date().toISOString().slice(0, 10)
    return `chart_${timestamp}`
  }
  
  return result
}

export function generateChartFilename(chartData, type = 'png') {
  const name = chartData?.name || chartData?.input?.name || '星盘'
  const date = chartData?.input?.date || chartData?.birth_date || ''
  
  const timestamp = new Date().toISOString().slice(0, 10)
  const timePart = new Date().toTimeString().slice(0, 5).replace(':', '')
  
  let filenameParts = []
  
  const cleanName = sanitizeFilename(name)
  if (cleanName) {
    filenameParts.push(cleanName)
  }
  
  if (date) {
    const cleanDate = sanitizeFilename(date).replace(/-/g, '')
    if (cleanDate && cleanDate.length >= 8) {
      filenameParts.push(cleanDate)
    }
  }
  
  if (filenameParts.length === 0) {
    filenameParts.push(timestamp)
    filenameParts.push(timePart)
  }
  
  return `${filenameParts.join('_')}.${type}`
}

export function downloadBlob(blob, filename) {
  if (!(blob instanceof Blob)) {
    console.error('downloadBlob: Invalid blob')
    return
  }
  
  const safeFilename = sanitizeFilename(filename)
  
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  
  link.download = safeFilename
  
  try {
    if (navigator.msSaveBlob) {
      navigator.msSaveBlob(blob, safeFilename)
      return
    }
  } catch (e) {
    console.log('IE saveBlob not available, using standard method')
  }
  
  document.body.appendChild(link)
  link.click()
  
  setTimeout(() => {
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)
  }, 100)
}

export function downloadBase64Pdf(base64Data, filename) {
  const byteCharacters = atob(base64Data)
  const byteNumbers = new Array(byteCharacters.length)
  
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i)
  }
  
  const byteArray = new Uint8Array(byteNumbers)
  const blob = new Blob([byteArray], { type: 'application/pdf' })
  
  downloadBlob(blob, filename)
}

export async function exportElementAsImage(
  element,
  options = {}
) {
  if (!element) {
    throw new Error('exportElementAsImage: Element is required')
  }
  
  const defaultOptions = {
    scale: 2,
    useCORS: true,
    logging: false,
    backgroundColor: '#0a0a1a',
    allowTaint: true,
    ignoreElements: (el) => {
      return el.classList && el.classList.contains('hide-on-export')
    },
    ...options
  }
  
  try {
    const originalOverflow = element.style.overflow
    const originalPosition = element.style.position
    
    element.style.overflow = 'visible'
    element.style.position = 'relative'
    
    const canvas = await html2canvas(element, defaultOptions)
    
    element.style.overflow = originalOverflow
    element.style.position = originalPosition
    
    return canvas
  } catch (error) {
    console.error('生成图片失败:', error)
    throw new Error(`生成图片失败: ${error.message}`)
  }
}

export async function exportAsPNG(
  element,
  filename = 'chart.png',
  options = {}
) {
  const canvas = await exportElementAsImage(element, options)
  
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (!blob) {
        reject(new Error('Failed to create PNG blob'))
        return
      }
      
      const safeFilename = sanitizeFilename(filename)
      downloadBlob(blob, safeFilename)
      resolve(canvas)
    }, 'image/png')
  })
}

export async function exportAsJPG(
  element,
  filename = 'chart.jpg',
  quality = 0.9,
  options = {}
) {
  const canvas = await exportElementAsImage(element, {
    ...options,
    backgroundColor: '#ffffff'
  })
  
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (!blob) {
        reject(new Error('Failed to create JPG blob'))
        return
      }
      
      const safeFilename = sanitizeFilename(filename)
      downloadBlob(blob, safeFilename)
      resolve(canvas)
    }, 'image/jpeg', quality)
  })
}

export function dataURLToBlob(dataURL) {
  if (!dataURL || !dataURL.includes(',')) {
    throw new Error('Invalid data URL')
  }
  
  const parts = dataURL.split(';base64,')
  const contentType = parts[0].split(':')[1]
  
  try {
    const raw = window.atob(parts[1])
    const rawLength = raw.length
    const uInt8Array = new Uint8Array(rawLength)
    
    for (let i = 0; i < rawLength; ++i) {
      uInt8Array[i] = raw.charCodeAt(i)
    }
    
    return new Blob([uInt8Array], { type: contentType || 'application/octet-stream' })
  } catch (error) {
    console.error('dataURLToBlob error:', error)
    throw new Error(`转换数据失败: ${error.message}`)
  }
}

export function getExportFormatById(id) {
  for (const key in EXPORT_FORMATS) {
    if (EXPORT_FORMATS[key].id === id) {
      return EXPORT_FORMATS[key]
    }
  }
  return EXPORT_FORMATS.PNG_STANDARD
}

export const EXPORT_FORMATS = {
  PNG_HD: {
    id: 'png_hd',
    name: '高清 PNG',
    format: 'png',
    scale: 3,
    quality: 1.0,
    description: '3倍分辨率，适合打印',
    mimeType: 'image/png'
  },
  PNG_STANDARD: {
    id: 'png_standard',
    name: '标准 PNG',
    format: 'png',
    scale: 2,
    quality: 1.0,
    description: '2倍分辨率，适合屏幕显示',
    mimeType: 'image/png'
  },
  PNG_THUMBNAIL: {
    id: 'png_thumbnail',
    name: '缩略图 PNG',
    format: 'png',
    scale: 1,
    quality: 1.0,
    description: '1倍分辨率，适合分享',
    mimeType: 'image/png'
  },
  JPG_HD: {
    id: 'jpg_hd',
    name: '高清 JPG',
    format: 'jpg',
    scale: 3,
    quality: 0.95,
    description: '3倍分辨率高画质',
    mimeType: 'image/jpeg'
  },
  JPG_STANDARD: {
    id: 'jpg_standard',
    name: '标准 JPG',
    format: 'jpg',
    scale: 2,
    quality: 0.9,
    description: '2倍分辨率标准画质',
    mimeType: 'image/jpeg'
  }
}
