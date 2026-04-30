import * as THREE from 'three'
import {
  THREE_ASTRO_CONFIG,
  PLANET_SCALE,
  PLANET_COLORS,
  PLANET_SYMBOLS,
  MAIN_PLANET_NAMES,
  PLANET_ORBIT_RADII,
  PLANET_Y_OFFSETS,
  longitudeTo3DPosition,
  disposeResource,
  createCanvasTexture,
  ASPECT_CONFIG,
  getAspectLineWidth,
  getAspectLineOpacity
} from './constants.js'

const MEMBER_COLORS = [
  0xff8c32, 0x50c8ff, 0x22c55e, 0xef4444, 0x8b5cf6,
  0xf59e0b, 0x06b6d4, 0xec4899, 0x6366f1, 0x10b981
]

export function useMultiMemberRenderer(getScene, getCamera, registerForDispose) {
  const memberPlanetMeshes = new Map()
  const crossMemberAspectLines = []
  const texturesToCleanup = []
  const meshesToCleanup = []
  const highlightedMemberIndex = { value: null }
  const highlightedPair = { value: null }

  function clearAll() {
    clearMemberPlanets()
    clearCrossMemberAspectLines()
  }

  function clearMemberPlanets() {
    const scene = getScene()
    if (!scene) return

    memberPlanetMeshes.forEach((meshes, memberIndex) => {
      meshes.forEach((mesh, planetName) => {
        scene.remove(mesh)
        if (mesh.userData.sunLight) {
          scene.remove(mesh.userData.sunLight)
        }
        if (mesh.userData.sunFlare) {
          scene.remove(mesh.userData.sunFlare)
        }
        if (mesh.userData.sunOuterFlare) {
          scene.remove(mesh.userData.sunOuterFlare)
        }
        if (mesh.userData.ring) {
          scene.remove(mesh.userData.ring)
        }
        if (mesh.userData.glow) {
          scene.remove(mesh.userData.glow)
        }
        if (mesh.userData.labelMesh) {
          scene.remove(mesh.userData.labelMesh)
        }
      })
    })

    memberPlanetMeshes.clear()
  }

  function clearCrossMemberAspectLines() {
    const scene = getScene()
    if (!scene) return

    crossMemberAspectLines.forEach(line => {
      scene.remove(line)
    })
    crossMemberAspectLines.length = 0
  }

  function renderMembers(members, focusedMemberIndex = null) {
    if (!members || members.length === 0) return

    clearMemberPlanets()

    members.forEach((member, memberIndex) => {
      const chart = member.chart
      if (!chart?.planets) return

      const memberColor = MEMBER_COLORS[memberIndex % MEMBER_COLORS.length]
      const isFocused = focusedMemberIndex === memberIndex

      const planetMeshes = new Map()

      chart.planets.forEach(planet => {
        const isMainPlanet = MAIN_PLANET_NAMES.includes(planet.name)
        const isNode = planet.name === '北交点' || planet.name === '南交点'

        if (!isMainPlanet && !isNode) return

        const mesh = createMemberPlanet(planet, memberIndex, memberColor, isFocused)
        if (mesh) {
          planetMeshes.set(planet.name, mesh)
          meshesToCleanup.push(mesh)

          const scene = getScene()
          if (scene) {
            scene.add(mesh)
          }
        }
      })

      memberPlanetMeshes.set(memberIndex, planetMeshes)
    })
  }

  function createMemberPlanet(planet, memberIndex, memberColor, isFocused) {
    const radius = PLANET_ORBIT_RADII[planet.name] || THREE_ASTRO_CONFIG.PLANET_ORBIT_RADIUS
    const yOffset = PLANET_Y_OFFSETS[planet.name] || 0
    
    const angleOffset = memberIndex * (Math.PI * 2 / 10)
    const position = longitudeTo3DPositionWithOffset(
      planet.longitude, 
      radius, 
      yOffset, 
      angleOffset,
      memberIndex
    )

    const scale = PLANET_SCALE[planet.name] || 0.5
    
    const memberColorInfo = {
      color: memberColor,
      emissive: adjustBrightness(memberColor, -40)
    }

    const geometryRadius = scale * 0.5
    const segments = THREE_ASTRO_CONFIG.PLANET_SEGMENTS

    const geometry = new THREE.SphereGeometry(geometryRadius, segments, segments)

    let material
    
    if (planet.name === '太阳') {
      material = new THREE.MeshStandardMaterial({
        color: memberColor,
        emissive: memberColorInfo.emissive,
        emissiveIntensity: 1.8,
        metalness: 0.1,
        roughness: 0.3
      })
    } else {
      material = new THREE.MeshStandardMaterial({
        color: memberColor,
        emissive: memberColorInfo.emissive,
        emissiveIntensity: 0.5,
        metalness: 0.25,
        roughness: 0.55
      })
    }

    const mesh = new THREE.Mesh(geometry, material)
    mesh.position.copy(position)
    mesh.castShadow = true
    mesh.receiveShadow = true

    mesh.userData = {
      planetName: planet.name,
      planetData: planet,
      memberIndex: memberIndex,
      memberColor: memberColor,
      originalScale: scale,
      originalEmissiveIntensity: planet.name === '太阳' ? 1.8 : 0.5,
      originalRadius: radius,
      originalYOffset: yOffset,
      isHovered: false,
      isSelected: false,
      isFocused: isFocused,
      angleOffset: angleOffset
    }

    if (registerForDispose) {
      registerForDispose({ geometry, material })
    }

    if (planet.name === '太阳') {
      addSunEffectsForMember(mesh, memberColor, memberIndex)
    } else if (planet.name === '土星') {
      addSaturnRingForMember(mesh, memberColor)
    }

    addMemberPlanetGlow(mesh, memberColor, geometryRadius, isFocused)

    const labelData = addMemberPlanetLabel(mesh, planet, radius, yOffset, memberIndex)
    if (labelData?.texture) {
      texturesToCleanup.push(labelData.texture)
    }

    return mesh
  }

  function adjustBrightness(color, amount) {
    const r = Math.max(0, Math.min(255, ((color >> 16) & 0xff) + amount))
    const g = Math.max(0, Math.min(255, ((color >> 8) & 0xff) + amount))
    const b = Math.max(0, Math.min(255, (color & 0xff) + amount))
    return (r << 16) | (g << 8) | b
  }

  function longitudeTo3DPositionWithOffset(longitude, radius, yOffset, angleOffset, memberIndex) {
    const baseAngle = longitude * Math.PI / 180
    const totalAngle = baseAngle + angleOffset
    
    const x = radius * Math.cos(totalAngle)
    const z = radius * Math.sin(totalAngle)
    
    const layerOffset = memberIndex * 0.5
    const y = yOffset + layerOffset

    return new THREE.Vector3(x, y, z)
  }

  function blendColors(color1, color2, ratio) {
    const r1 = (color1 >> 16) & 0xff
    const g1 = (color1 >> 8) & 0xff
    const b1 = color1 & 0xff
    const r2 = (color2 >> 16) & 0xff
    const g2 = (color2 >> 8) & 0xff
    const b2 = color2 & 0xff

    const r = Math.round(r1 + (r2 - r1) * ratio)
    const g = Math.round(g1 + (g2 - g1) * ratio)
    const b = Math.round(b1 + (b2 - b1) * ratio)

    return (r << 16) | (g << 8) | b
  }

  function addSunEffectsForMember(mesh, memberColor, memberIndex) {
    const scene = getScene()
    if (!scene) return

    const light = new THREE.PointLight(memberColor, 2.0, 25)
    light.position.copy(mesh.position)
    scene.add(light)
    mesh.userData.sunLight = light

    const flareGeometry = new THREE.SphereGeometry(0.85, 32, 32)
    const flareMaterial = new THREE.MeshBasicMaterial({
      color: memberColor,
      transparent: true,
      opacity: 0.35
    })
    const flare = new THREE.Mesh(flareGeometry, flareMaterial)
    flare.position.copy(mesh.position)
    mesh.userData.sunFlare = flare
    scene.add(flare)

    const outerFlareGeometry = new THREE.SphereGeometry(1.2, 32, 32)
    const outerFlareMaterial = new THREE.MeshBasicMaterial({
      color: memberColor,
      transparent: true,
      opacity: 0.15,
      side: THREE.BackSide
    })
    const outerFlare = new THREE.Mesh(outerFlareGeometry, outerFlareMaterial)
    outerFlare.position.copy(mesh.position)
    mesh.userData.sunOuterFlare = outerFlare
    scene.add(outerFlare)

    if (registerForDispose) {
      registerForDispose({ geometry: flareGeometry, material: flareMaterial })
      registerForDispose({ geometry: outerFlareGeometry, material: outerFlareMaterial })
    }
  }

  function addSaturnRingForMember(mesh, memberColor) {
    const scene = getScene()
    if (!scene) return

    const ringGeometry = new THREE.RingGeometry(0.6, 1.0, 32)
    const ringMaterial = new THREE.MeshBasicMaterial({
      color: memberColor,
      transparent: true,
      opacity: 0.6,
      side: THREE.DoubleSide
    })
    const ring = new THREE.Mesh(ringGeometry, ringMaterial)
    ring.rotation.x = Math.PI / 2.5
    ring.position.copy(mesh.position)
    scene.add(ring)
    mesh.userData.ring = ring

    if (registerForDispose) {
      registerForDispose({ geometry: ringGeometry, material: ringMaterial })
    }
  }

  function addMemberPlanetGlow(mesh, color, radius, isFocused) {
    const scene = getScene()
    if (!scene) return

    const glowRadius = radius * 2.5
    const glowGeometry = new THREE.SphereGeometry(glowRadius, 16, 16)
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: color,
      transparent: true,
      opacity: isFocused ? 0.15 : 0.08,
      side: THREE.BackSide
    })
    const glow = new THREE.Mesh(glowGeometry, glowMaterial)
    glow.position.copy(mesh.position)
    scene.add(glow)
    mesh.userData.glow = glow

    if (registerForDispose) {
      registerForDispose({ geometry: glowGeometry, material: glowMaterial })
    }
  }

  function addMemberPlanetLabel(mesh, planet, radius, yOffset, memberIndex) {
    const scene = getScene()
    if (!scene) return null

    const symbol = PLANET_SYMBOLS[planet.name] || ''
    const memberColor = MEMBER_COLORS[memberIndex % MEMBER_COLORS.length]
    
    const canvas = document.createElement('canvas')
    canvas.width = 64
    canvas.height = 64
    const ctx = canvas.getContext('2d')
    
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)'
    ctx.beginPath()
    ctx.arc(32, 32, 28, 0, Math.PI * 2)
    ctx.fill()
    
    ctx.strokeStyle = `#${memberColor.toString(16).padStart(6, '0')}`
    ctx.lineWidth = 2
    ctx.stroke()
    
    ctx.font = 'bold 24px Arial'
    ctx.fillStyle = '#ffffff'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(symbol, 32, 32)

    const texture = new THREE.CanvasTexture(canvas)
    const material = new THREE.SpriteMaterial({
      map: texture,
      transparent: true,
      opacity: 0.9
    })
    const sprite = new THREE.Sprite(material)
    
    const labelPosition = mesh.position.clone()
    labelPosition.y += 0.8
    sprite.position.copy(labelPosition)
    sprite.scale.set(1.2, 1.2, 1.2)

    scene.add(sprite)
    mesh.userData.labelMesh = sprite

    if (registerForDispose) {
      registerForDispose({ material })
    }

    return { texture, sprite }
  }

  function renderCrossMemberAspects(members, matrix) {
    if (!members || members.length < 2 || !matrix?.pairs) return

    clearCrossMemberAspectLines()

    const scene = getScene()
    if (!scene) return

    matrix.pairs.forEach(pair => {
      const nameA = pair.pair[0]
      const nameB = pair.pair[1]
      const idxA = members.findIndex(m => m.name === nameA)
      const idxB = members.findIndex(m => m.name === nameB)

      if (idxA < 0 || idxB < 0) return

      const aspects = pair.aspects || []
      aspects.forEach(aspect => {
        if (aspect.aspect === '合相') return

        const lineMesh = createCrossMemberAspectLine(
          aspect, 
          idxA, 
          idxB, 
          aspect.planet_a, 
          aspect.planet_b
        )
        if (lineMesh) {
          crossMemberAspectLines.push(lineMesh)
          meshesToCleanup.push(lineMesh)
          scene.add(lineMesh)
        }
      })
    })
  }

  function createCrossMemberAspectLine(aspect, memberIdxA, memberIdxB, planetNameA, planetNameB) {
    const meshesA = memberPlanetMeshes.get(memberIdxA)
    const meshesB = memberPlanetMeshes.get(memberIdxB)

    if (!meshesA || !meshesB) return null

    const planetMeshA = meshesA.get(planetNameA)
    const planetMeshB = meshesB.get(planetNameB)

    if (!planetMeshA || !planetMeshB) return null

    const aspectType = aspect.aspect
    const orb = aspect.orb || 0
    const nature = aspect.nature || 'neutral'

    let lineColor
    if (nature === 'harmonious') {
      lineColor = aspectType === '三分相' ? 0x22c55e : 0x3b82f6
    } else if (nature === 'challenging') {
      lineColor = 0xef4444
    } else {
      lineColor = 0xfbbf24
    }

    const start = planetMeshA.position.clone()
    const end = planetMeshB.position.clone()

    const lineWidth = getAspectLineWidth(aspectType, orb) * 0.8
    const baseOpacity = getAspectLineOpacity(aspectType, orb, false)

    const midPoint = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5)
    
    const arcHeight = 2.0 + Math.random() * 1.0
    
    const curve = new THREE.QuadraticBezierCurve3(
      start,
      new THREE.Vector3(midPoint.x, arcHeight + (start.y + end.y) * 0.5, midPoint.z),
      end
    )

    const segments = THREE_ASTRO_CONFIG.ASPECT_LINE_SEGMENTS
    const tubeGeometry = new THREE.TubeGeometry(curve, segments, lineWidth * 0.4, 6, false)

    const lineMaterial = new THREE.MeshBasicMaterial({
      color: lineColor,
      transparent: true,
      opacity: baseOpacity
    })

    const lineMesh = new THREE.Mesh(tubeGeometry, lineMaterial)
    lineMesh.userData = {
      aspectData: aspect,
      memberIndexA: memberIdxA,
      memberIndexB: memberIdxB,
      planetA: planetNameA,
      planetB: planetNameB,
      originalOpacity: baseOpacity,
      highlightedOpacity: 0.9,
      isHighlighted: false,
      lineWidth: lineWidth,
      nature: nature
    }

    if (registerForDispose) {
      registerForDispose({ geometry: tubeGeometry, material: lineMaterial })
    }

    return lineMesh
  }

  function highlightMember(memberIndex) {
    highlightedMemberIndex.value = memberIndex
    highlightedPair.value = null

    memberPlanetMeshes.forEach((meshes, idx) => {
      const isHighlighted = idx === memberIndex
      meshes.forEach(mesh => {
        updateMeshHighlight(mesh, isHighlighted)
      })
    })

    crossMemberAspectLines.forEach(line => {
      const isConnected = line.userData.memberIndexA === memberIndex || 
                         line.userData.memberIndexB === memberIndex
      updateLineHighlight(line, isConnected)
    })
  }

  function highlightPair(memberIndexA, memberIndexB) {
    highlightedMemberIndex.value = null
    highlightedPair.value = { a: memberIndexA, b: memberIndexB }

    memberPlanetMeshes.forEach((meshes, idx) => {
      const isHighlighted = idx === memberIndexA || idx === memberIndexB
      meshes.forEach(mesh => {
        updateMeshHighlight(mesh, isHighlighted)
      })
    })

    crossMemberAspectLines.forEach(line => {
      const isConnected = (line.userData.memberIndexA === memberIndexA && line.userData.memberIndexB === memberIndexB) ||
                         (line.userData.memberIndexA === memberIndexB && line.userData.memberIndexB === memberIndexA)
      updateLineHighlight(line, isConnected)
    })
  }

  function clearHighlights() {
    highlightedMemberIndex.value = null
    highlightedPair.value = null

    memberPlanetMeshes.forEach(meshes => {
      meshes.forEach(mesh => {
        updateMeshHighlight(mesh, false)
      })
    })

    crossMemberAspectLines.forEach(line => {
      updateLineHighlight(line, false)
    })
  }

  function updateMeshHighlight(mesh, isHighlighted) {
    if (!mesh || !mesh.material) return

    const material = mesh.material

    if (isHighlighted) {
      mesh.scale.setScalar(1.3)
      if (material.emissiveIntensity !== undefined) {
        material.emissiveIntensity = mesh.userData.originalEmissiveIntensity * 1.5
      }
      material.opacity = 1.0
      
      if (mesh.userData.glow) {
        mesh.userData.glow.material.opacity = 0.25
      }
    } else {
      mesh.scale.setScalar(1.0)
      if (material.emissiveIntensity !== undefined) {
        material.emissiveIntensity = mesh.userData.originalEmissiveIntensity
      }
      material.opacity = 0.4
      
      if (mesh.userData.glow) {
        mesh.userData.glow.material.opacity = 0.04
      }
    }

    mesh.userData.isHighlighted = isHighlighted
  }

  function updateLineHighlight(line, isHighlighted) {
    if (!line || !line.material) return

    const material = line.material

    if (isHighlighted) {
      material.opacity = line.userData.highlightedOpacity
      line.scale.setScalar(1.5)
    } else {
      material.opacity = line.userData.originalOpacity * 0.3
      line.scale.setScalar(1.0)
    }

    line.userData.isHighlighted = isHighlighted
  }

  function getMemberPlanetMesh(memberIndex, planetName) {
    const meshes = memberPlanetMeshes.get(memberIndex)
    return meshes ? meshes.get(planetName) : null
  }

  function getAllMeshes() {
    const allMeshes = []
    memberPlanetMeshes.forEach(meshes => {
      meshes.forEach(mesh => allMeshes.push(mesh))
    })
    return allMeshes
  }

  function updatePlanetAnimations() {
    memberPlanetMeshes.forEach(meshes => {
      meshes.forEach(mesh => {
        if (mesh.rotation) {
          mesh.rotation.y += 0.002
        }
      })
    })
  }

  function dispose() {
    clearAll()
    
    texturesToCleanup.forEach(texture => {
      disposeResource(texture)
    })
    texturesToCleanup.length = 0
  }

  return {
    renderMembers,
    renderCrossMemberAspects,
    clearAll,
    highlightMember,
    highlightPair,
    clearHighlights,
    getMemberPlanetMesh,
    getAllMeshes,
    updatePlanetAnimations,
    highlightedMemberIndex,
    highlightedPair,
    dispose
  }
}
