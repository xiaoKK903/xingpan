import * as THREE from 'three'
import {
  THREE_ASTRO_CONFIG,
  ASPECT_CONFIG,
  ASPECT_PATTERN_CONFIG,
  ASPECT_SYMBOLS,
  ASPECT_NATURES,
  MAIN_PLANET_NAMES,
  getAspectLineWidth,
  getAspectLineOpacity,
  disposeResource
} from './constants.js'

const MAJOR_ASPECT_NAMES = ['合相', '对分相', '四分相', '三分相', '六分相']

export function useAspectLineRenderer(getScene, getPlanetMesh, registerForDispose) {
  const aspectLines = []
  const highlightedAspectLines = []
  const patternMeshes = []
  const meshesToCleanup = []
  
  function createAspectLines(chartData) {
    if (!chartData?.aspects) return
    
    clearAspectLines()
    
    const aspects = chartData.aspects
    
    aspects.forEach(aspect => {
      if (!MAJOR_ASPECT_NAMES.includes(aspect.aspect)) return
      
      const planet1Mesh = getPlanetMesh(aspect.planet1)
      const planet2Mesh = getPlanetMesh(aspect.planet2)
      
      if (!planet1Mesh || !planet2Mesh) return
      
      const lineMesh = createSingleAspectLine(aspect, planet1Mesh, planet2Mesh)
      if (lineMesh) {
        aspectLines.push(lineMesh)
        meshesToCleanup.push(lineMesh)
        
        const scene = getScene()
        if (scene) {
          scene.add(lineMesh)
        }
      }
    })
    
    detectAndRenderPatterns(chartData)
  }
  
  function createSingleAspectLine(aspect, planet1Mesh, planet2Mesh) {
    const config = ASPECT_CONFIG[aspect.aspect] || ASPECT_CONFIG['合相']
    const orb = aspect.orb || 0
    
    const start = planet1Mesh.position.clone()
    const end = planet2Mesh.position.clone()
    
    const lineWidth = getAspectLineWidth(aspect.aspect, orb)
    const baseOpacity = getAspectLineOpacity(aspect.aspect, orb, false)
    const highlightedOpacity = config.highlightedOpacity
    
    const midPoint = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5)
    
    const startY = start.y
    const endY = end.y
    const arcHeight = Math.max(0.3, Math.abs(startY - endY) * 0.5 + 0.2)
    
    const curve = new THREE.QuadraticBezierCurve3(
      start,
      new THREE.Vector3(midPoint.x, arcHeight + (startY + endY) * 0.5, midPoint.z),
      end
    )
    
    const segments = THREE_ASTRO_CONFIG.ASPECT_LINE_SEGMENTS
    const tubeGeometry = new THREE.TubeGeometry(curve, segments, lineWidth * 0.5, 8, false)
    
    const lineMaterial = new THREE.MeshBasicMaterial({
      color: config.color,
      transparent: true,
      opacity: baseOpacity
    })
    
    const lineMesh = new THREE.Mesh(tubeGeometry, lineMaterial)
    lineMesh.userData = {
      aspectData: aspect,
      planet1: aspect.planet1,
      planet2: aspect.planet2,
      originalOpacity: baseOpacity,
      highlightedOpacity: highlightedOpacity,
      isHighlighted: false,
      orb: orb,
      lineWidth: lineWidth
    }
    
    if (registerForDispose) {
      registerForDispose({ geometry: tubeGeometry, material: lineMaterial })
    }
    
    return lineMesh
  }
  
  function detectAndRenderPatterns(chartData) {
    if (!chartData?.aspects) return
    
    const patterns = detectAspectPatterns(chartData)
    
    patterns.forEach(pattern => {
      const patternMesh = createPatternVisualization(pattern)
      if (patternMesh) {
        patternMeshes.push(patternMesh)
        
        const scene = getScene()
        if (scene) {
          scene.add(patternMesh)
        }
      }
    })
  }
  
  function hasAspect(aspects, planet1, planet2, aspectType) {
    return aspects.some(a => 
      (a.planet1 === planet1 && a.planet2 === planet2 || a.planet1 === planet2 && a.planet2 === planet1) &&
      a.aspect === aspectType
    )
  }
  
  function getPlanetsFromAspects(aspectList) {
    const planets = new Set()
    aspectList.forEach(a => {
      planets.add(a.planet1)
      planets.add(a.planet2)
    })
    return planets
  }
  
  function detectAspectPatterns(chartData) {
    if (!chartData?.aspects) return []
    
    const patterns = []
    const aspects = chartData.aspects.filter(a => MAJOR_ASPECT_NAMES.includes(a.aspect))
    
    const trines = aspects.filter(a => a.aspect === '三分相')
    const usedPlanets = new Set()
    
    for (let i = 0; i < trines.length; i++) {
      for (let j = i + 1; j < trines.length; j++) {
        for (let k = j + 1; k < trines.length; k++) {
          const planets = new Set()
          planets.add(trines[i].planet1)
          planets.add(trines[i].planet2)
          planets.add(trines[j].planet1)
          planets.add(trines[j].planet2)
          planets.add(trines[k].planet1)
          planets.add(trines[k].planet2)
          
          if (planets.size === 3) {
            const hasOverlap = [...planets].some(p => usedPlanets.has(p))
            if (!hasOverlap) {
              patterns.push({
                type: '大三角',
                planets: Array.from(planets),
                aspects: [trines[i], trines[j], trines[k]]
              })
              planets.forEach(p => usedPlanets.add(p))
            }
          }
        }
      }
    }
    
    const oppositions = aspects.filter(a => a.aspect === '对分相')
    const squares = aspects.filter(a => a.aspect === '四分相')
    const sextiles = aspects.filter(a => a.aspect === '六分相')
    
    for (let i = 0; i < oppositions.length; i++) {
      for (let j = i + 1; j < oppositions.length; j++) {
        const opp1Planets = new Set([oppositions[i].planet1, oppositions[i].planet2])
        const opp2Planets = new Set([oppositions[j].planet1, oppositions[j].planet2])
        
        const allPlanets = new Set([...opp1Planets, ...opp2Planets])
        if (allPlanets.size === 4) {
          let squareCount = 0
          const squareAspects = []
          const planetList = [...allPlanets]
          
          for (let p = 0; p < planetList.length; p++) {
            for (let q = p + 1; q < planetList.length; q++) {
              const square = squares.find(s =>
                (s.planet1 === planetList[p] && s.planet2 === planetList[q]) ||
                (s.planet1 === planetList[q] && s.planet2 === planetList[p])
              )
              if (square) {
                squareCount++
                squareAspects.push(square)
              }
            }
          }
          
          if (squareCount >= 4) {
            const hasOverlap = [...allPlanets].some(p => usedPlanets.has(p))
            if (!hasOverlap) {
              patterns.push({
                type: '大十字',
                planets: [...allPlanets],
                aspects: [oppositions[i], oppositions[j], ...squareAspects.slice(0, 4)]
              })
              allPlanets.forEach(p => usedPlanets.add(p))
            }
          }
        }
      }
    }
    
    oppositions.forEach(opposition => {
      const oppPlanets = [opposition.planet1, opposition.planet2]
      
      const availablePlanets = [...new Set(
        aspects
          .filter(a => a.planet1 !== opposition.planet1 || a.planet2 !== opposition.planet2)
          .flatMap(a => [a.planet1, a.planet2])
      )].filter(p => p !== opposition.planet1 && p !== opposition.planet2)
      
      availablePlanets.forEach(thirdPlanet => {
        const sextile1 = sextiles.find(s =>
          (s.planet1 === oppPlanets[0] && s.planet2 === thirdPlanet) ||
          (s.planet1 === thirdPlanet && s.planet2 === oppPlanets[0])
        )
        const sextile2 = sextiles.find(s =>
          (s.planet1 === oppPlanets[1] && s.planet2 === thirdPlanet) ||
          (s.planet1 === thirdPlanet && s.planet2 === oppPlanets[1])
        )
        
        if (sextile1 && sextile2) {
          const allPlanets = new Set([...oppPlanets, thirdPlanet])
          const hasOverlap = [...allPlanets].some(p => usedPlanets.has(p))
          if (!hasOverlap) {
            patterns.push({
              type: 'T三角',
              planets: [...allPlanets],
              aspects: [opposition, sextile1, sextile2]
            })
            allPlanets.forEach(p => usedPlanets.add(p))
          }
        }
      })
    })
    
    trines.forEach(trine1 => {
      const trine1Planets = [trine1.planet1, trine1.planet2]
      
      trines.forEach(trine2 => {
        if (trine1 === trine2) return
        
        const trine2Planets = [trine2.planet1, trine2.planet2]
        
        const common = trine1Planets.filter(p => trine2Planets.includes(p))
        if (common.length === 1) {
          const apex = common[0]
          const planet1 = trine1Planets.find(p => p !== apex)
          const planet2 = trine2Planets.find(p => p !== apex)
          
          const hasSextile = sextiles.some(s =>
            (s.planet1 === planet1 && s.planet2 === planet2) ||
            (s.planet1 === planet2 && s.planet2 === planet1)
          )
          
          if (hasSextile && planet1 && planet2) {
            const allPlanets = new Set([apex, planet1, planet2])
            const hasOverlap = [...allPlanets].some(p => usedPlanets.has(p))
            if (!hasOverlap) {
              patterns.push({
                type: 'Yod',
                planets: [...allPlanets],
                aspects: [trine1, trine2]
              })
              allPlanets.forEach(p => usedPlanets.add(p))
            }
          }
        }
      })
    })
    
    return patterns
  }
  
  function createPatternVisualization(pattern) {
    const config = ASPECT_PATTERN_CONFIG[pattern.type] || ASPECT_PATTERN_CONFIG['大三角']
    const scene = getScene()
    
    if (!scene) return null
    
    const group = new THREE.Group()
    
    const planetMeshes = pattern.planets.map(name => getPlanetMesh(name)).filter(Boolean)
    
    if (planetMeshes.length < 3) return null
    
    const center = new THREE.Vector3()
    planetMeshes.forEach(m => center.add(m.position))
    center.divideScalar(planetMeshes.length)
    
    const shape = new THREE.Shape()
    const firstPos = planetMeshes[0].position
    shape.moveTo(firstPos.x, firstPos.z)
    for (let i = 1; i < planetMeshes.length; i++) {
      shape.lineTo(planetMeshes[i].position.x, planetMeshes[i].position.z)
    }
    shape.lineTo(firstPos.x, firstPos.z)
    
    const extrudeSettings = {
      steps: 1,
      depth: 0.1,
      bevelEnabled: false
    }
    
    const shapeGeometry = new THREE.ExtrudeGeometry(shape, extrudeSettings)
    shapeGeometry.rotateX(-Math.PI / 2)
    shapeGeometry.translate(0, center.y - 0.05, 0)
    
    const shapeMaterial = new THREE.MeshBasicMaterial({
      color: config.fillColor,
      transparent: true,
      opacity: config.fillOpacity,
      side: THREE.DoubleSide
    })
    
    const shapeMesh = new THREE.Mesh(shapeGeometry, shapeMaterial)
    group.add(shapeMesh)
    
    planetMeshes.forEach((mesh, index) => {
      const nextMesh = planetMeshes[(index + 1) % planetMeshes.length]
      
      const curve = new THREE.QuadraticBezierCurve3(
        mesh.position,
        new THREE.Vector3(
          (mesh.position.x + nextMesh.position.x) / 2,
          (mesh.position.y + nextMesh.position.y) / 2 + 0.5,
          (mesh.position.z + nextMesh.position.z) / 2
        ),
        nextMesh.position
      )
      
      const tubeGeometry = new THREE.TubeGeometry(curve, 16, config.lineWidth * 0.6, 8, false)
      const tubeMaterial = new THREE.MeshBasicMaterial({
        color: config.color,
        transparent: true,
        opacity: config.opacity
      })
      
      const tube = new THREE.Mesh(tubeGeometry, tubeMaterial)
      group.add(tube)
      
      if (registerForDispose) {
        registerForDispose({ geometry: tubeGeometry, material: tubeMaterial })
      }
    })
    
    if (registerForDispose) {
      registerForDispose({ geometry: shapeGeometry, material: shapeMaterial })
    }
    
    group.userData = { type: 'pattern', patternType: pattern.type, planets: pattern.planets }
    
    return group
  }
  
  function updateAspectLines(chartData) {
    createAspectLines(chartData)
  }
  
  function clearAspectLines() {
    const scene = getScene()
    
    meshesToCleanup.forEach(line => {
      if (scene) {
        scene.remove(line)
      }
      disposeResource(line)
    })
    
    patternMeshes.forEach(pattern => {
      if (scene) {
        scene.remove(pattern)
      }
      disposeResource(pattern)
    })
    
    meshesToCleanup.length = 0
    patternMeshes.length = 0
    aspectLines.length = 0
    highlightedAspectLines.length = 0
  }
  
  function highlightAspectLinesForPlanet(planetName) {
    clearHighlightedAspectLines()
    
    aspectLines.forEach(line => {
      const matches = (line.userData.planet1 === planetName || line.userData.planet2 === planetName)
      
      if (matches) {
        line.material.opacity = line.userData.highlightedOpacity
        line.userData.isHighlighted = true
        highlightedAspectLines.push(line)
        
        const scale = line.userData.lineWidth / getAspectLineWidth(line.userData.aspectData.aspect, line.userData.orb)
        line.scale.setScalar(1.5 * scale)
      }
    })
  }
  
  function clearHighlightedAspectLines() {
    highlightedAspectLines.forEach(line => {
      line.material.opacity = line.userData.originalOpacity
      line.userData.isHighlighted = false
      line.scale.setScalar(1.0)
    })
    highlightedAspectLines.length = 0
  }
  
  function getAspectsForPlanet(planetName, chartData) {
    if (!chartData?.aspects) return []
    
    const planetAspects = []
    
    chartData.aspects.forEach(aspect => {
      if (!MAJOR_ASPECT_NAMES.includes(aspect.aspect)) return
      
      if (aspect.planet1 === planetName || aspect.planet2 === planetName) {
        const otherPlanet = aspect.planet1 === planetName ? aspect.planet2 : aspect.planet1
        
        planetAspects.push({
          otherPlanet,
          type: aspect.aspect,
          symbol: ASPECT_SYMBOLS[aspect.aspect] || '○',
          nature: ASPECT_NATURES[aspect.aspect] || 'neutral',
          orb: aspect.orb
        })
      }
    })
    
    return planetAspects.sort((a, b) => (a.orb || 0) - (b.orb || 0))
  }
  
  function dispose() {
    clearAspectLines()
  }
  
  return {
    aspectLines,
    highlightedAspectLines,
    createAspectLines,
    updateAspectLines,
    clearAspectLines,
    highlightAspectLinesForPlanet,
    clearHighlightedAspectLines,
    getAspectsForPlanet,
    detectAndRenderPatterns,
    dispose
  }
}
