import React, { useRef, useMemo, useState, useEffect } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { EffectComposer, Bloom } from '@react-three/postprocessing'
import * as THREE from 'three'
import { NovaStaticFallback } from './NovaFallback'

// Palette values (Light 3D Glassmorphism - Blue accents)
const COLOR_CREAM = '#F8FAFC'
const COLOR_DARK = '#0B0F19'
const COLOR_ACCENT = '#3B82F6'
const COLOR_PRIMARY = '#2563EB'
const COLOR_GOLD = '#60A5FA'

// Expression configurations
const EXPRESSIONS = {
  idle: {
    eyeScale: [1, 1.25, 0.5],
    eyeColor: COLOR_ACCENT,
    emissiveIntensity: 3.5,
    speed: 1.6,
  },
  happy: {
    eyeScale: [1.3, 0.55, 0.5],
    eyeColor: COLOR_GOLD,
    emissiveIntensity: 4.2,
    speed: 2.0,
  },
  thinking: {
    eyeScale: [0.95, 1.05, 0.5],
    eyeColor: '#FFD54F',
    emissiveIntensity: 3.0,
    speed: 1.2,
  },
  analyzing: {
    eyeScale: [1.2, 1.2, 0.6],
    eyeColor: '#FF5722',
    emissiveIntensity: 5.5,
    speed: 3.0,
  },
}

function NovaModel({ expression = 'idle', size = 'hero' }) {
  const groupRef = useRef()
  const headRef = useRef()
  const leftEyeRef = useRef()
  const rightEyeRef = useRef()
  const ringRef = useRef()
  const chestCoreRef = useRef()
  const timeRef = useRef(0)

  const activeExp = EXPRESSIONS[expression] || EXPRESSIONS.idle

  useFrame((state, delta) => {
    timeRef.current += delta * activeExp.speed
    const t = timeRef.current

    if (groupRef.current) {
      // Gentle floating animation
      groupRef.current.position.y = Math.sin(t * 1.5) * 0.08
      // Subtle natural breathing yaw
      groupRef.current.rotation.y = Math.sin(t * 0.7) * 0.12
      // Very slight pitch sway
      groupRef.current.rotation.x = Math.sin(t * 1.1) * 0.03
    }

    if (ringRef.current) {
      // Warm floor ember ring gentle pulse
      const pulse = 1 + Math.sin(t * 2.2) * 0.08
      ringRef.current.scale.set(pulse, pulse, 1)
    }

    if (chestCoreRef.current) {
      const corePulse = 3.0 + Math.sin(t * 2.8) * 1.2
      if (chestCoreRef.current.material) {
        chestCoreRef.current.material.emissiveIntensity = corePulse
      }
    }

    // Eye pulsing when analyzing
    if (expression === 'analyzing') {
      const eyePulse = 4.5 + Math.sin(t * 6.0) * 1.5
      if (leftEyeRef.current?.material) {
        leftEyeRef.current.material.emissiveIntensity = eyePulse
      }
      if (rightEyeRef.current?.material) {
        rightEyeRef.current.material.emissiveIntensity = eyePulse
      }
    }
  })

  // Head material (matte ceramic / cream)
  const headMat = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: COLOR_CREAM,
        roughness: 0.28,
        metalness: 0.08,
      }),
    []
  )

  // Face visor material (glossy dark glass)
  const visorMat = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: COLOR_DARK,
        roughness: 0.12,
        metalness: 0.85,
      }),
    []
  )

  // Glowing eyes material
  const eyeMat = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: activeExp.eyeColor,
        emissive: activeExp.eyeColor,
        emissiveIntensity: activeExp.emissiveIntensity,
        roughness: 0.2,
      }),
    [activeExp]
  )

  // Glowing ember base ring material
  const ringMat = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: COLOR_PRIMARY,
        emissive: COLOR_PRIMARY,
        emissiveIntensity: 4.5,
        roughness: 0.3,
      }),
    []
  )

  // Dark metallic joints / accents
  const darkMetalMat = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: '#1A1824',
        roughness: 0.35,
        metalness: 0.7,
      }),
    []
  )

  // Gold accent rings
  const goldAccentMat = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: '#60A5FA',
        metalness: 0.6,
        roughness: 0.25,
      }),
    []
  )

  const scaleMultiplier = size === 'hero' ? 1.15 : 0.95

  return (
    <group ref={groupRef} scale={[scaleMultiplier, scaleMultiplier, scaleMultiplier]}>
      {/* ---------- HEAD & FACE ---------- */}
      <group ref={headRef} position={[0, 0.45, 0]}>
        {/* Main Head Shell (Pill / Capsule) */}
        <mesh material={headMat} castShadow>
          <sphereGeometry args={[0.9, 36, 36]} />
        </mesh>

        {/* Glossy Black Visor Inset */}
        <mesh position={[0, 0.04, 0.32]} material={visorMat}>
          <sphereGeometry args={[0.74, 32, 32, 0, Math.PI * 2, 0, Math.PI * 0.48]} />
        </mesh>

        {/* Left Eye */}
        <mesh
          ref={leftEyeRef}
          position={[-0.32, 0.08, 0.86]}
          scale={activeExp.eyeScale}
          material={eyeMat}
        >
          <sphereGeometry args={[0.13, 24, 24]} />
        </mesh>

        {/* Right Eye */}
        <mesh
          ref={rightEyeRef}
          position={[0.32, 0.08, 0.86]}
          scale={activeExp.eyeScale}
          material={eyeMat}
        >
          <sphereGeometry args={[0.13, 24, 24]} />
        </mesh>

        {/* Side Ear Cuffs (Left & Right) */}
        <group position={[-0.92, 0.05, 0]} rotation={[0, 0, Math.PI / 2]}>
          <mesh material={headMat}>
            <cylinderGeometry args={[0.22, 0.22, 0.14, 28]} />
          </mesh>
          <mesh position={[0, 0.08, 0]} material={goldAccentMat}>
            <torusGeometry args={[0.18, 0.03, 16, 32]} />
          </mesh>
        </group>

        <group position={[0.92, 0.05, 0]} rotation={[0, 0, -Math.PI / 2]}>
          <mesh material={headMat}>
            <cylinderGeometry args={[0.22, 0.22, 0.14, 28]} />
          </mesh>
          <mesh position={[0, 0.08, 0]} material={goldAccentMat}>
            <torusGeometry args={[0.18, 0.03, 16, 32]} />
          </mesh>
        </group>
      </group>

      {/* ---------- NECK ---------- */}
      <mesh position={[0, -0.4, 0]} material={darkMetalMat}>
        <cylinderGeometry args={[0.42, 0.46, 0.2, 28]} />
      </mesh>

      {/* ---------- TORSO / BODY ---------- */}
      <group position={[0, -0.95, 0]}>
        {/* Main Chest Shell */}
        <mesh material={headMat}>
          <cylinderGeometry args={[0.55, 0.48, 0.9, 32]} />
        </mesh>

        {/* Upper chest curve */}
        <mesh position={[0, 0.42, 0]} material={headMat}>
          <sphereGeometry args={[0.55, 32, 16, 0, Math.PI * 2, 0, Math.PI * 0.5]} />
        </mesh>

        {/* Chest Reactor Core */}
        <mesh
          ref={chestCoreRef}
          position={[0, 0.05, 0.51]}
          material={
            new THREE.MeshStandardMaterial({
              color: COLOR_ACCENT,
              emissive: COLOR_ACCENT,
              emissiveIntensity: 3.5,
              roughness: 0.2,
            })
          }
        >
          <sphereGeometry args={[0.11, 24, 24]} />
        </mesh>

        {/* Core Ring Bezel */}
        <mesh position={[0, 0.05, 0.48]} material={goldAccentMat}>
          <torusGeometry args={[0.16, 0.025, 16, 32]} />
        </mesh>

        {/* Arms (Resting Calm Pose) */}
        <mesh position={[-0.68, -0.05, 0]} rotation={[0, 0, 0.15]} material={headMat}>
          <capsuleGeometry args={[0.12, 0.5, 16, 16]} />
        </mesh>
        <mesh position={[0.68, -0.05, 0]} rotation={[0, 0, -0.15]} material={headMat}>
          <capsuleGeometry args={[0.12, 0.5, 16, 16]} />
        </mesh>
      </group>

      {/* ---------- BASE FLOATING EMBER RING ---------- */}
      <group ref={ringRef} position={[0, -1.65, 0]} rotation={[Math.PI / 2, 0, 0]}>
        {/* Glowing Ember Torus */}
        <mesh material={ringMat}>
          <torusGeometry args={[0.82, 0.045, 20, 48]} />
        </mesh>
        {/* Soft Inner Glow Disc */}
        <mesh position={[0, 0, -0.01]}>
          <ringGeometry args={[0.01, 0.8, 36]} />
          <meshBasicMaterial
            color={COLOR_PRIMARY}
            transparent
            opacity={0.18}
            side={THREE.DoubleSide}
          />
        </mesh>
      </group>
    </group>
  )
}

export default function Nova({ expression = 'idle', size = 'hero', className = '' }) {
  const [reducedMotion, setReducedMotion] = useState(false)
  const [hasWebGlError, setHasWebGlError] = useState(false)

  useEffect(() => {
    try {
      const media = window.matchMedia('(prefers-reduced-motion: reduce)')
      setReducedMotion(media.matches)
      const listener = (e) => setReducedMotion(e.matches)
      media.addEventListener('change', listener)
      return () => media.removeEventListener('change', listener)
    } catch {
      // Ignore if matchMedia not supported
    }
  }, [])

  if (reducedMotion || hasWebGlError) {
    return <NovaStaticFallback size={size} expression={expression} className={className} />
  }

  const isHero = size === 'hero'
  const containerHeight = isHero ? 'h-[460px] sm:h-[520px]' : 'h-[130px]'
  const cameraZ = isHero ? 4.5 : 4.0
  const cameraFov = isHero ? 42 : 46

  return (
    <div
      className={`relative w-full ${containerHeight} flex items-center justify-center pointer-events-none select-none ${className}`}
    >
      <Canvas
        camera={{ position: [0, 0, cameraZ], fov: cameraFov }}
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: 'high-performance',
        }}
        onCreated={({ gl }) => {
          gl.toneMapping = THREE.ACESFilmicToneMapping
          gl.toneMappingExposure = 1.15
        }}
        onError={() => setHasWebGlError(true)}
      >
        <ambientLight intensity={0.9} color="#FFF8F0" />
        <directionalLight position={[4, 5, 5]} intensity={1.6} color="#FFFFFF" />
        <directionalLight position={[-4, 2, -2]} intensity={1.4} color="#60A5FA" />
        <pointLight position={[0, -1.8, 0]} intensity={4.5} distance={5} color="#2563EB" />

        <NovaModel expression={expression} size={size} />

        <EffectComposer multisampling={0} disableNormalPass>
          <Bloom
            luminanceThreshold={0.55}
            luminanceSmoothing={0.8}
            intensity={1.3}
            mipmapBlur
          />
        </EffectComposer>
      </Canvas>
    </div>
  )
}
