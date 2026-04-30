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
  createCanvasTexture
} from './constants.js'

export function usePlanetRenderer(getScene, getCamera, registerForDispose) {
  const planetMeshes = new Map()
  const texturesToCleanup = []
  const meshesToCleanup = []
  
  function createPlanets(chartData) {
    if (!chartData?.planets) return
    
    clearPlanets()
    
    const planets = chartData.planets
    
    planets.forEach(planet => {
      const isMainPlanet = MAIN_PLANET_NAMES.includes(planet.name)
      const isNode = planet.name === '北交点' || planet.name === '南交点'
      
      if (!isMainPlanet && !isNode) return
      
      const mesh = createSinglePlanet(planet)
      if (mesh) {
        planetMeshes.set(planet.name, mesh)
        meshesToCleanup.push(mesh)
        
        const scene = getScene()
        if (scene) {
          scene.add(mesh)
        }
      }
    })
  }
  
  function createSinglePlanet(planet) {
    const radius = PLANET_ORBIT_RADII[planet.name] || THREE_ASTRO_CONFIG.PLANET_ORBIT_RADIUS
    const yOffset = PLANET_Y_OFFSETS[planet.name] || 0
    const position = longitudeTo3DPosition(planet.longitude, radius, yOffset)
    
    const scale = PLANET_SCALE[planet.name] || 0.5
    const colorInfo = PLANET_COLORS[planet.name] || { color: 0x888888, emissive: 0x222222 }
    
    const geometryRadius = scale * 0.5
    const segments = THREE_ASTRO_CONFIG.PLANET_SEGMENTS
    
    const geometry = new THREE.SphereGeometry(geometryRadius, segments, segments)
    
    let material
    if (planet.name === '太阳') {
      material = new THREE.MeshStandardMaterial({
        color: colorInfo.color,
        emissive: colorInfo.emissive,
        emissiveIntensity: 1.2,
        metalness: 0.1,
        roughness: 0.3
      })
    } else {
      material = new THREE.MeshStandardMaterial({
        color: colorInfo.color,
        emissive: colorInfo.emissive,
        emissiveIntensity: 0.35,
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
      originalScale: scale,
      originalEmissiveIntensity: planet.name === '太阳' ? 1.2 : 0.35,
      originalRadius: radius,
      originalYOffset: yOffset,
      isHovered: false,
      isSelected: false
    }
    
    if (registerForDispose) {
      registerForDispose({ geometry, material })
    }
    
    if (planet.name === '太阳') {
      addSunEffects(mesh, colorInfo)
    } else if (planet.name === '土星') {
      addSaturnRing(mesh)
    }
    
    addPlanetGlow(mesh, colorInfo.color, geometryRadius)
    
    const labelData = addPlanetLabel(mesh, planet, radius, yOffset)
    if (labelData?.texture) {
      texturesToCleanup.push(labelData.texture)
    }
    
    return mesh
  }
  
  function addSunEffects(mesh, colorInfo) {
    const scene = getScene()
    if (!scene) return
    
    const light = new THREE.PointLight(colorInfo.color, 2.5, 25)
    light.position.copy(mesh.position)
    scene.add(light)
    mesh.userData.sunLight = light
    
    const flareGeometry = new THREE.SphereGeometry(0.85, 32, 32)
    const flareMaterial = new THREE.MeshBasicMaterial({
      color: 0xffaa00,
      transparent: true,
      opacity: 0.35
    })
    const flare = new THREE.Mesh(flareGeometry, flareMaterial)
    flare.position.copy(mesh.position)
    mesh.userData.sunFlare = flare
    scene.add(flare)
    
    const outerFlareGeometry = new THREE.SphereGeometry(1.2, 32, 32)
    const outerFlareMaterial = new THREE.MeshBasicMaterial({
      color: 0xffdd88,
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
  
  function addSaturnRing(planetMesh) {
    const ringGeometry = new THREE.RingGeometry(0.5, 0.95, 64)
    const ringMaterial = new THREE.MeshStandardMaterial({
      color: 0xc9b896,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.75,
      metalness: 0.5,
      roughness: 0.55
    })
    const ring = new THREE.Mesh(ringGeometry, ringMaterial)
    ring.rotation.x = Math.PI / 2.5
    planetMesh.add(ring)
    
    const innerRingGeometry = new THREE.RingGeometry(0.4, 0.48, 64)
    const innerRingMaterial = new THREE.MeshStandardMaterial({
      color: 0xb09070,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.6,
      metalness: 0.45,
      roughness: 0.6
    })
    const innerRing = new THREE.Mesh(innerRingGeometry, innerRingMaterial)
    innerRing.rotation.x = Math.PI / 2.5
    planetMesh.add(innerRing)
    
    if (registerForDispose) {
      registerForDispose({ geometry: ringGeometry, material: ringMaterial })
      registerForDispose({ geometry: innerRingGeometry, material: innerRingMaterial })
    }
  }
  
  function addPlanetGlow(mesh, color, radius) {
    const glowGeometry = new THREE.SphereGeometry(radius * 1.6, 24, 24)
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: color,
      transparent: true,
      opacity: 0.18,
      side: THREE.BackSide
    })
    const glow = new THREE.Mesh(glowGeometry, glowMaterial)
    mesh.add(glow)
    mesh.userData.glowMesh = glow
    
    if (registerForDispose) {
      registerForDispose({ geometry: glowGeometry, material: glowMaterial })
    }
  }
  
  function addPlanetLabel(mesh, planet, orbitRadius, yOffset) {
    const { canvas, texture } = createCanvasTexture(256, 64, (ctx) => {
      ctx.clearRect(0, 0, 256, 64)
      ctx.font = 'bold 26px Arial'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      
      const colorInfo = PLANET_COLORS[planet.name]
      const colorHex = '#' + colorInfo.color.toString(16).padStart(6, '0')
      
      ctx.fillStyle = 'rgba(15, 15, 35, 0.9)'
      ctx.beginPath()
      if (ctx.roundRect) {
        ctx.roundRect(28, 10, 200, 44, 8)
      } else {
        ctx.rect(28, 10, 200, 44)
      }
      ctx.fill()
      
      ctx.strokeStyle = colorHex + '88'
      ctx.lineWidth = 1.5
      ctx.stroke()
      
      ctx.fillStyle = '#ffffff'
      const symbol = PLANET_SYMBOLS[planet.name] || '★'
      const text = symbol + ' ' + planet.name
      ctx.fillText(text, 128, 32)
    })
    
    const spriteMaterial = new THREE.SpriteMaterial({
      map: texture,
      transparent: true,
      opacity: 0
    })
    const sprite = new THREE.Sprite(spriteMaterial)
    
    const geometryRadius = mesh.geometry.parameters.radius
    const labelOffset = geometryRadius * 2.5 + 0.6
    
    sprite.position.set(0, labelOffset, 0)
    sprite.scale.set(3.2, 0.8, 1)
    
    mesh.add(sprite)
    mesh.userData.labelSprite = sprite
    
    if (registerForDispose) {
      registerForDispose({ texture, material: spriteMaterial })
    }
    
    return { texture, sprite }
  }
  
  function updatePlanets(chartData) {
    createPlanets(chartData)
  }
  
  function clearPlanets() {
    const scene = getScene()
    
    meshesToCleanup.forEach(mesh => {
      if (mesh.userData.sunLight) {
        if (scene) {
          scene.remove(mesh.userData.sunLight)
        }
        mesh.userData.sunLight = null
      }
      if (mesh.userData.sunFlare) {
        if (scene) {
          scene.remove(mesh.userData.sunFlare)
        }
        disposeResource(mesh.userData.sunFlare)
        mesh.userData.sunFlare = null
      }
      if (mesh.userData.sunOuterFlare) {
        if (scene) {
          scene.remove(mesh.userData.sunOuterFlare)
        }
        disposeResource(mesh.userData.sunOuterFlare)
        mesh.userData.sunOuterFlare = null
      }
      if (scene) {
        scene.remove(mesh)
      }
      disposeResource(mesh)
    })
    
    texturesToCleanup.forEach(t => disposeResource(t))
    
    meshesToCleanup.length = 0
    texturesToCleanup.length = 0
    planetMeshes.clear()
  }
  
  function getPlanetMesh(planetName) {
    return planetMeshes.get(planetName)
  }
  
  function getAllPlanetMeshes() {
    return Array.from(planetMeshes.values())
  }
  
  function highlightPlanet(planetName, isSelected = false) {
    const mesh = planetMeshes.get(planetName)
    if (!mesh) return
    
    if (isSelected) {
      mesh.userData.isSelected = true
      mesh.userData.isHovered = false
    } else {
      mesh.userData.isHovered = true
    }
    
    mesh.scale.setScalar(1.35)
    mesh.material.emissiveIntensity = 1.0
    
    if (mesh.userData.glowMesh) {
      mesh.userData.glowMesh.material.opacity = 0.35
    }
    
    if (mesh.userData.labelSprite) {
      mesh.userData.labelSprite.material.opacity = 0.92
    }
    
    const scene = getScene()
    if (mesh.userData.sunLight && scene) {
      mesh.userData.sunLight.intensity = 3.5
    }
  }
  
  function resetPlanetHighlight(planetName) {
    const mesh = planetMeshes.get(planetName)
    if (!mesh) return
    
    if (mesh.userData.isSelected || mesh.userData.isHovered) {
      mesh.userData.isSelected = false
      mesh.userData.isHovered = false
      mesh.scale.setScalar(1.0)
      mesh.material.emissiveIntensity = mesh.userData.originalEmissiveIntensity
      
      if (mesh.userData.glowMesh) {
        mesh.userData.glowMesh.material.opacity = 0.18
      }
      
      if (mesh.userData.labelSprite) {
        mesh.userData.labelSprite.material.opacity = 0
      }
      
      const scene = getScene()
      if (mesh.userData.sunLight && scene) {
        mesh.userData.sunLight.intensity = 2.5
      }
    }
  }
  
  function resetAllPlanets() {
    planetMeshes.forEach(mesh => {
      resetPlanetHighlight(mesh.userData.planetName)
    })
  }
  
  function updatePlanetAnimations() {
    const camera = getCamera()
    
    planetMeshes.forEach(mesh => {
      mesh.rotation.y += 0.006
      
      if (mesh.userData.labelSprite && camera) {
        mesh.userData.labelSprite.quaternion.copy(camera.quaternion)
      }
      
      if (mesh.userData.sunFlare && camera) {
        const distance = mesh.position.distanceTo(camera.position)
        const scaleFactor = Math.max(0.8, Math.min(1.2, distance / 20))
        mesh.userData.sunFlare.scale.setScalar(scaleFactor)
      }
    })
  }
  
  function dispose() {
    clearPlanets()
  }
  
  return {
    planetMeshes,
    createPlanets,
    updatePlanets,
    clearPlanets,
    getPlanetMesh,
    getAllPlanetMeshes,
    highlightPlanet,
    resetPlanetHighlight,
    resetAllPlanets,
    updatePlanetAnimations,
    dispose
  }
}
